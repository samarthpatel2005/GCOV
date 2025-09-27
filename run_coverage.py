#!/usr/bin/env python3
"""
Enhanced GitHub Coverage Generator Launcher v2.0
Python script to start the coverage generation flow
Replaces run_coverage.bat with Python implementation
"""

import os
import sys
import subprocess
import argparse
import platform
from pathlib import Path
import webbrowser
import time


def print_banner():
    """Print the application banner"""
    print("=" * 50)
    print("Enhanced GitHub Coverage Generator v2.0")
    print("With LLM Integration for Non-Compatible Repos")
    print("=" * 50)
    print()


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("ERROR: Python 3.7 or later is required")
        print(f"Current version: Python {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def run_command(command, description="", check_error=True):
    """Run a system command with error handling"""
    if description:
        print(f"🔄 {description}...")
    
    try:
        if platform.system() == "Windows":
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        else:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if check_error and result.returncode != 0:
            print(f"❌ Error running command: {command}")
            print(f"Error output: {result.stderr}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Exception running command: {command}")
        print(f"Exception: {e}")
        return False


def setup_virtual_environment():
    """Setup virtual environment if it doesn't exist"""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        if not run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
            return False
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")
    
    return True


def activate_virtual_environment():
    """Activate virtual environment by updating PATH and Python executable"""
    venv_path = Path("venv")
    
    if platform.system() == "Windows":
        venv_python = venv_path / "Scripts" / "python.exe"
        venv_pip = venv_path / "Scripts" / "pip.exe"
        scripts_path = venv_path / "Scripts"
    else:
        venv_python = venv_path / "bin" / "python"
        venv_pip = venv_path / "bin" / "pip"
        scripts_path = venv_path / "bin"
    
    if venv_python.exists():
        # Update environment PATH
        os.environ["PATH"] = str(scripts_path) + os.pathsep + os.environ["PATH"]
        os.environ["VIRTUAL_ENV"] = str(venv_path.absolute())
        
        # Update Python executable for subprocess calls
        sys.executable = str(venv_python)
        
        print("✅ Virtual environment activated")
        return str(venv_python), str(venv_pip)
    else:
        print("❌ Virtual environment Python not found")
        return None, None


def install_requirements(pip_executable):
    """Install or update requirements"""
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("⚠️  requirements.txt not found, skipping package installation")
        return True
    
    print("📦 Installing/updating requirements...")
    command = f'"{pip_executable}" install -r requirements.txt'
    
    if not run_command(command, "Installing packages"):
        print("❌ Failed to install requirements")
        return False
    
    print("✅ Requirements installed successfully")
    return True


def run_coverage_generator(python_executable, repo_url=None):
    """Run the main coverage generator"""
    script_path = Path("generate_coverage.py")
    
    if not script_path.exists():
        print("❌ generate_coverage.py not found!")
        return False
    
    # Build command
    if repo_url:
        command = f'"{python_executable}" generate_coverage.py "{repo_url}"'
        print(f"🚀 Using repository URL: {repo_url}")
    else:
        command = f'"{python_executable}" generate_coverage.py'
        print("🚀 Using repository URL from config.ini...")
    
    print("🔄 Starting coverage generation...")
    print("-" * 50)
    
    # Set up environment for Unicode support
    env = os.environ.copy()
    if platform.system() == "Windows":
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONLEGACYWINDOWSSTDIO"] = "0"
    
    # Run the coverage generator with real-time output
    try:
        if platform.system() == "Windows":
            # For Windows, use chcp 65001 for UTF-8 support
            process = subprocess.Popen(
                f'chcp 65001 >nul && {command}',
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                encoding='utf-8',
                errors='replace',  # Replace problematic characters
                bufsize=1, 
                universal_newlines=True, 
                env=env
            )
        else:
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                bufsize=1, 
                universal_newlines=True,
                env=env
            )
        
        # Print output in real-time with encoding safety
        for line in iter(process.stdout.readline, ''):
            if line:
                try:
                    print(line.rstrip())
                except UnicodeEncodeError:
                    # Fallback for problematic characters
                    safe_line = line.encode('ascii', 'replace').decode('ascii')
                    print(safe_line.rstrip())
        
        process.wait()
        
        if process.returncode == 0:
            print("-" * 50)
            print("✅ SUCCESS: Coverage report generated!")
            return True
        else:
            print("-" * 50)
            print("❌ ERROR: Coverage generation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Exception running coverage generator: {e}")
        return False


def open_coverage_report():
    """Open the generated coverage report in browser"""
    report_paths = [
        Path("coverage_output") / "index.html",
        Path("test_coverage_output") / "index.html"
    ]
    
    for report_path in report_paths:
        if report_path.exists():
            print(f"🌐 Opening coverage report: {report_path}")
            try:
                webbrowser.open(f"file://{report_path.absolute()}")
                return True
            except Exception as e:
                print(f"⚠️  Could not open browser: {e}")
                print(f"📄 Report available at: {report_path.absolute()}")
                return True
    
    print("❌ No coverage report found to open")
    return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Enhanced GitHub Repository Coverage Generator Launcher v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_coverage.py
  python run_coverage.py https://github.com/user/repo.git
  python run_coverage.py --no-browser https://github.com/user/repo.git
        """
    )
    
    parser.add_argument(
        'repo_url', 
        nargs='?', 
        help='GitHub repository URL (optional - uses config.ini if not provided)'
    )
    
    parser.add_argument(
        '--no-browser', 
        action='store_true',
        help='Do not open the coverage report in browser'
    )
    
    parser.add_argument(
        '--output-dir',
        default='coverage_output',
        help='Output directory for coverage report (default: coverage_output)'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    print(f"📁 Working directory: {script_dir}")
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        print("❌ Failed to setup virtual environment")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Activate virtual environment
    python_exe, pip_exe = activate_virtual_environment()
    if not python_exe or not pip_exe:
        print("❌ Failed to activate virtual environment")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Install requirements
    if not install_requirements(pip_exe):
        print("❌ Failed to install requirements")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Run coverage generator
    success = run_coverage_generator(python_exe, args.repo_url)
    
    if success:
        print("\n🎉 Coverage generation completed successfully!")
        
        # Open report in browser unless disabled
        if not args.no_browser:
            print("⏳ Opening report in browser in 2 seconds...")
            time.sleep(2)
            open_coverage_report()
        else:
            print("📄 Coverage report ready (browser opening disabled)")
    else:
        print("\n❌ Coverage generation failed!")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Wait for user input before closing
    print("\nPress Enter to exit...")
    input()


if __name__ == "__main__":
    main()