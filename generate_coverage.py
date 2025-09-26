#!/usr/bin/env python3
"""
Enhanced GitHub Repository Code Coverage Generator with LLM Integration
Supports both Gcov-compatible and non-compatible repositories using AWS Bedrock
"""

import os
import sys
import subprocess
import shutil
import tempfile
import json
import argparse
import re
import configparser
from pathlib import Path
import urllib.parse
from typing import Dict, List, Tuple, Optional

# Import our LLM assistant
from llm_coverage_assistant import LLMCoverageAssistant


class EnhancedCoverageGeneratorV2:
    def __init__(self, repo_url, output_dir="coverage_output", config_path="config.ini"):
        self.repo_url = repo_url
        self.output_dir = Path(output_dir)
        self.temp_dir = None
        self.repo_name = self._extract_repo_name()
        self.has_lcov = self._check_lcov()
        self.config_path = config_path
        
        # Load configuration
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        # Initialize LLM assistant
        self.llm_assistant = LLMCoverageAssistant(config_path)
        
        # Track modifications for rollback
        self.applied_modifications = []
        
    def _extract_repo_name(self):
        """Extract repository name from URL"""
        parsed = urllib.parse.urlparse(self.repo_url)
        path = parsed.path.strip('/')
        if path.endswith('.git'):
            path = path[:-4]
        return path.split('/')[-1]
    
    def _check_lcov(self):
        """Check if LCOV is available"""
        try:
            result = subprocess.run(["lcov", "--version"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _run_command(self, cmd, cwd=None, capture_output=True):
        """Run shell command and return result"""
        try:
            print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                capture_output=capture_output, 
                text=True,
                shell=True if os.name == 'nt' else False
            )
            if result.returncode != 0 and capture_output:
                print(f"Error: {result.stderr}")
            return result
        except Exception as e:
            print(f"Command failed: {e}")
            return None
    
    def generate_coverage_report(self):
        """Main method to generate coverage report with LLM assistance"""
        print("=" * 60)
        print(">> Enhanced GitHub Repository Coverage Generator v2.0")
        print("=" * 60)
        
        try:
            # Step 1: Clone repository
            repo_path = self.clone_repository()
            if not repo_path:
                return False
            
            # Step 2: Analyze repository structure
            print("\n>> Analyzing repository structure...")
            analysis = self.llm_assistant.analyze_repository_structure(repo_path)
            self._print_analysis(analysis)
            
            # Step 3: Check Gcov compatibility
            print("\n>> Checking Gcov compatibility...")
            is_compatible, issues = self.llm_assistant.check_gcov_compatibility(repo_path, analysis)
            
            if is_compatible:
                print("SUCCESS: Repository is Gcov-compatible!")
                return self._generate_direct_coverage(repo_path, analysis)
            else:
                print("WARNING: Repository is NOT Gcov-compatible")
                print("Issues found:")
                for issue in issues:
                    print(f"  - {issue}")
                
                return self._generate_llm_assisted_coverage(repo_path, analysis, issues)
        
        except Exception as e:
            print(f"ERROR: Error generating coverage report: {e}")
            return False
        finally:
            # Always cleanup
            self._cleanup()
    
    def _print_analysis(self, analysis: Dict):
        """Print repository analysis results"""
        print(f"  Project Type: {analysis['project_type']}")
        print(f"  Build System: {analysis['build_system']}")
        print(f"  Languages: {', '.join(analysis['languages'])}")
        print(f"  Source Files: {len(analysis['source_files'])} files")
        print(f"  Test Files: {len(analysis['test_files'])} files")
        print(f"  Build Files: {len(analysis['build_files'])} files")
    
    def _generate_direct_coverage(self, repo_path: Path, analysis: Dict) -> bool:
        """Generate coverage for Gcov-compatible repositories"""
        print("\n>> Generating coverage for Gcov-compatible repository...")
        
        # Build with coverage
        if not self._build_with_coverage(repo_path, analysis):
            print("ERROR: Failed to build with coverage")
            return False
        
        # Run tests and generate coverage
        if not self._run_tests_and_coverage(repo_path, analysis):
            print("ERROR: Failed to run tests and generate coverage")
            return False
        
        # Generate HTML report
        return self._generate_html_report(repo_path)
    
    def _generate_llm_assisted_coverage(self, repo_path: Path, analysis: Dict, issues: List[str]) -> bool:
        """Generate coverage for non-compatible repositories using LLM assistance"""
        print("\n🤖 Using LLM to make repository Gcov-compatible...")
        
        # Generate modifications using LLM
        modifications = self.llm_assistant.generate_gcov_modifications(repo_path, analysis, issues)
        
        print("📝 LLM Generated Modifications:")
        print(f"  Explanation: {modifications.get('explanation', 'No explanation provided')}")
        
        # Ask user for confirmation
        if not self._confirm_modifications(modifications):
            print("❌ User cancelled modifications")
            return False
        
        # Apply modifications temporarily
        print("\n⚙️  Applying temporary modifications...")
        self.applied_modifications = self.llm_assistant.apply_modifications_temporarily(repo_path, modifications)
        
        try:
            # Build with coverage
            print("\n🔨 Building with coverage (after modifications)...")
            if not self._build_with_coverage(repo_path, analysis, use_llm_modifications=True, modifications=modifications):
                print("❌ Failed to build with coverage after modifications")
                return False
            
            # Run tests and generate coverage
            if not self._run_tests_and_coverage(repo_path, analysis, modifications=modifications):
                print("❌ Failed to run tests and generate coverage")
                return False
            
            # Generate HTML report
            success = self._generate_html_report(repo_path)
            
            if success:
                print("\n✅ Successfully generated coverage report with LLM assistance!")
                print("📄 Note: Modifications were applied temporarily and will be rolled back")
            
            return success
            
        except Exception as e:
            print(f"❌ Error during LLM-assisted coverage generation: {e}")
            return False
    
    def _confirm_modifications(self, modifications: Dict) -> bool:
        """Ask user to confirm modifications (for now, auto-confirm in demo mode)"""
        # In a real implementation, you might want to show the user the changes
        # and ask for confirmation. For demo purposes, we'll auto-confirm.
        
        mod_data = modifications.get("modifications", {})
        
        print("  Modifications to be applied:")
        if mod_data.get("makefile_changes"):
            print(f"    - Makefile: {len(mod_data['makefile_changes'])} changes")
        if mod_data.get("cmake_changes"):
            print(f"    - CMake: {len(mod_data['cmake_changes'])} changes")
        if mod_data.get("missing_files"):
            print(f"    - New files: {len(mod_data['missing_files'])} files")
        
        # Auto-confirm for demo (in production, ask user)
        auto_apply = self.config.getboolean('AWS_BEDROCK', 'auto_apply_suggestions', fallback=False)
        if auto_apply:
            print("  ✅ Auto-applying modifications (configured in config.ini)")
            return True
        else:
            # For demo purposes, always return True
            # In production, implement proper user confirmation
            print("  ✅ Applying modifications (demo mode)")
            return True
    
    def _build_with_coverage(self, repo_path: Path, analysis: Dict, use_llm_modifications=False, modifications=None) -> bool:
        """Build project with coverage instrumentation"""
        print("🔨 Building project with coverage instrumentation...")
        
        if analysis['project_type'] in ['c', 'c++', 'c/c++']:
            return self._build_c_cpp_with_coverage(repo_path, analysis, use_llm_modifications, modifications)
        else:
            print(f"❌ Coverage generation not implemented for {analysis['project_type']}")
            return False
    
    def _build_c_cpp_with_coverage(self, repo_path: Path, analysis: Dict, use_llm_modifications=False, modifications=None) -> bool:
        """Build C/C++ project with gcov coverage"""
        coverage_flags = [
            "-fprofile-arcs",
            "-ftest-coverage", 
            "-g",
            "-O0"
        ]
        
        # Set environment variables for coverage
        env = os.environ.copy()
        env['CFLAGS'] = ' '.join(coverage_flags)
        env['CXXFLAGS'] = ' '.join(coverage_flags)
        env['LDFLAGS'] = "-lgcov"
        
        try:
            if analysis['build_system'] == 'make' or (repo_path / "Makefile").exists():
                # Clean and build with make
                print("  Using Make build system...")
                self._run_command(["make", "clean"], cwd=repo_path)
                
                if use_llm_modifications and modifications:
                    # Try to use LLM-suggested compilation
                    mod_data = modifications.get("modifications", {})
                    test_compilation = mod_data.get("test_compilation", "")
                    if test_compilation:
                        print(f"  Using LLM-suggested compilation: {test_compilation}")
                        result = self._run_command([test_compilation], cwd=repo_path, capture_output=False)
                        if result and result.returncode == 0:
                            return True
                
                # Try mingw32-make first, then make
                for make_cmd in ["mingw32-make", "make"]:
                    result = self._run_command([make_cmd], cwd=repo_path, capture_output=False)
                    if result and result.returncode == 0:
                        return True
                    print(f"  ⚠️  {make_cmd} failed, trying next option...")
                
                print("  ⚠️  Make commands failed, falling back to direct compilation")
                return self._compile_simple_project(repo_path, analysis, coverage_flags)
                
            elif analysis['build_system'] == 'cmake' or (repo_path / "CMakeLists.txt").exists():
                # Build with cmake
                print("  Using CMake build system...")
                build_dir = repo_path / "build"
                build_dir.mkdir(exist_ok=True)
                
                # Configure
                cmake_cmd = ["cmake", "..", f"-DCMAKE_C_FLAGS={' '.join(coverage_flags)}", 
                           f"-DCMAKE_CXX_FLAGS={' '.join(coverage_flags)}"]
                result = self._run_command(cmake_cmd, cwd=build_dir)
                if not result or result.returncode != 0:
                    return False
                
                # Build
                result = self._run_command(["cmake", "--build", "."], cwd=build_dir, capture_output=False)
                return result and result.returncode == 0
                
            else:
                # Simple compilation for projects without build system
                print("  Using simple compilation...")
                return self._compile_simple_project(repo_path, analysis, coverage_flags)
                
        except Exception as e:
            print(f"❌ Build failed: {e}")
            return False
    
    def _compile_simple_project(self, repo_path: Path, analysis: Dict, coverage_flags: List[str]) -> bool:
        """Compile simple projects without build system"""
        c_files = [f for f in analysis['source_files'] if f.endswith('.c')]
        cpp_files = [f for f in analysis['source_files'] if f.endswith(('.cpp', '.cc', '.cxx'))]
        
        compiled_any = False
        
        if c_files:
            print(f"  Compiling C files: {c_files}")
            for i, c_file in enumerate(c_files):
                exe_name = f"test_program_{i}.exe"
                compile_cmd = ["gcc"] + coverage_flags + [c_file] + ["-lgcov", "-o", exe_name]
                result = self._run_command(compile_cmd, cwd=repo_path)
                if result and result.returncode == 0:
                    print(f"    ✅ Compiled {c_file} → {exe_name}")
                    compiled_any = True
                else:
                    print(f"    ❌ Failed to compile {c_file}")
        
        if cpp_files:
            print(f"  Compiling C++ files: {cpp_files}")
            for i, cpp_file in enumerate(cpp_files):
                exe_name = f"test_program_cpp_{i}.exe"
                compile_cmd = ["g++"] + coverage_flags + [cpp_file] + ["-lgcov", "-o", exe_name]
                result = self._run_command(compile_cmd, cwd=repo_path)
                if result and result.returncode == 0:
                    print(f"    ✅ Compiled {cpp_file} → {exe_name}")
                    compiled_any = True
                else:
                    print(f"    ❌ Failed to compile {cpp_file}")
        
        return compiled_any
    
    def _run_tests_and_coverage(self, repo_path: Path, analysis: Dict, modifications=None) -> bool:
        """Run tests and generate coverage data"""
        print("🧪 Running tests and generating coverage data...")
        
        # Look for executables to run
        executables = list(repo_path.glob("*.exe")) + list(repo_path.glob("test*")) + list((repo_path / "build").glob("*.exe") if (repo_path / "build").exists() else [])
        
        if not executables:
            print("  ⚠️  No executables found to run for testing")
            # Try to generate some coverage data anyway by running gcov on source files
            return self._generate_coverage_data_directly(repo_path, analysis)
        
        # Run executables
        for exe in executables:
            if exe.is_file() and os.access(exe, os.X_OK):
                print(f"  Running: {exe.name}")
                try:
                    result = self._run_command([str(exe)], cwd=repo_path, capture_output=False)
                    if result and result.returncode == 0:
                        print(f"    ✅ {exe.name} executed successfully")
                    else:
                        print(f"    ⚠️  {exe.name} execution failed, but continuing...")
                except:
                    print(f"    ⚠️  Could not execute {exe.name}")
        
        # Generate coverage data
        return self._generate_coverage_data_directly(repo_path, analysis, modifications)
    
    def _generate_coverage_data_directly(self, repo_path: Path, analysis: Dict, modifications=None) -> bool:
        """Generate coverage data using gcov"""
        print("📊 Generating coverage data with gcov...")
        
        # Look for .gcda and .gcno files
        gcda_files = list(repo_path.rglob("*.gcda"))
        gcno_files = list(repo_path.rglob("*.gcno"))
        
        print(f"  Found {len(gcda_files)} .gcda files and {len(gcno_files)} .gcno files")
        
        if not gcda_files and not gcno_files:
            print("  ⚠️  No coverage data files found, trying to generate anyway...")
        
        # Run gcov on source files - individual files for Windows compatibility
        source_files = [f for f in analysis['source_files'] if f.endswith(('.c', '.cpp', '.cc'))]
        gcov_commands = []
        for src_file in source_files:
            gcov_commands.append(f"gcov {src_file}")
        
        # Fallback commands if no source files found
        if not gcov_commands:
            gcov_commands = ["gcov main.c", "gcov *.c"]
        
        # Use LLM-suggested gcov commands if available
        if modifications:
            mod_data = modifications.get("modifications", {})
            llm_commands = mod_data.get("gcov_commands", [])
            if llm_commands:
                gcov_commands = llm_commands
                print(f"  Using LLM-suggested gcov commands: {llm_commands}")
        
        success = False
        for cmd in gcov_commands:
            try:
                # Split command for proper execution
                cmd_parts = cmd.split()
                result = self._run_command(cmd_parts, cwd=repo_path)
                if result and result.returncode == 0:
                    success = True
                    print(f"    ✅ {cmd} executed successfully")
                else:
                    print(f"    ⚠️  {cmd} failed, trying next...")
            except:
                print(f"    ⚠️  Could not execute {cmd}")
        
        # Check for .gcov files
        gcov_files = list(repo_path.rglob("*.gcov"))
        print(f"  Generated {len(gcov_files)} .gcov files")
        
        return success or len(gcov_files) > 0
    
    def _generate_html_report(self, repo_path: Path) -> bool:
        """Generate HTML coverage report"""
        print("📄 Generating HTML coverage report...")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.has_lcov:
            return self._generate_lcov_report(repo_path)
        else:
            return self._generate_custom_html_report(repo_path)
    
    def _generate_lcov_report(self, repo_path: Path) -> bool:
        """Generate report using LCOV"""
        try:
            # Capture coverage data
            lcov_cmd = ["lcov", "--capture", "--directory", ".", "--output-file", "coverage.info"]
            result = self._run_command(lcov_cmd, cwd=repo_path)
            
            if not result or result.returncode != 0:
                print("  ❌ LCOV capture failed")
                return False
            
            # Generate HTML
            genhtml_cmd = ["genhtml", "coverage.info", "--output-directory", str(self.output_dir)]
            result = self._run_command(genhtml_cmd, cwd=repo_path)
            
            if result and result.returncode == 0:
                print(f"  ✅ HTML report generated in {self.output_dir}")
                return True
            else:
                print("  ❌ genhtml failed")
                return False
                
        except Exception as e:
            print(f"  ❌ LCOV report generation failed: {e}")
            return False
    
    def _generate_custom_html_report(self, repo_path: Path) -> bool:
        """Generate custom HTML report from .gcov files"""
        print("  Using custom HTML generator...")
        
        gcov_files = list(repo_path.rglob("*.gcov"))
        if not gcov_files:
            print("  ❌ No .gcov files found")
            return False
        
        # Parse .gcov files and generate HTML
        coverage_data = self._parse_gcov_files(gcov_files)
        html_content = self._generate_html_content(coverage_data)
        
        # Write HTML report
        report_file = self.output_dir / "index.html"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(html_content, encoding='utf-8')
        
        print(f"  ✅ Custom HTML report generated: {report_file}")
        return True
    
    def _parse_gcov_files(self, gcov_files: List[Path]) -> Dict:
        """Parse .gcov files to extract coverage data"""
        coverage_data = {
            'files': [],
            'total_lines': 0,
            'covered_lines': 0,
            'coverage_percentage': 0
        }
        
        for gcov_file in gcov_files:
            try:
                with open(gcov_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                file_data = {
                    'name': gcov_file.stem,
                    'lines': [],
                    'total_lines': 0,
                    'covered_lines': 0
                }
                
                for line in lines:
                    if line.strip():
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            execution_count = parts[0].strip()
                            line_number = parts[1].strip()
                            source_line = parts[2] if len(parts) > 2 else ""
                            
                            if line_number.isdigit():
                                file_data['total_lines'] += 1
                                coverage_data['total_lines'] += 1
                                
                                if execution_count.isdigit() and int(execution_count) > 0:
                                    file_data['covered_lines'] += 1
                                    coverage_data['covered_lines'] += 1
                                
                                file_data['lines'].append({
                                    'number': int(line_number),
                                    'count': execution_count,
                                    'source': source_line.rstrip()
                                })
                
                if file_data['total_lines'] > 0:
                    file_data['coverage_percentage'] = (file_data['covered_lines'] / file_data['total_lines']) * 100
                    coverage_data['files'].append(file_data)
                
            except Exception as e:
                print(f"  ⚠️  Error parsing {gcov_file}: {e}")
        
        if coverage_data['total_lines'] > 0:
            coverage_data['coverage_percentage'] = (coverage_data['covered_lines'] / coverage_data['total_lines']) * 100
        
        return coverage_data
    
    def _generate_html_content(self, coverage_data: Dict) -> str:
        """Generate HTML content for coverage report"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Code Coverage Report - {self.repo_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .file {{ margin: 10px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .coverage-high {{ background-color: #d4edda; }}
        .coverage-medium {{ background-color: #fff3cd; }}
        .coverage-low {{ background-color: #f8d7da; }}
        .line {{ font-family: monospace; font-size: 12px; }}
        .line-covered {{ background-color: #d4edda; }}
        .line-uncovered {{ background-color: #f8d7da; }}
        .line-number {{ color: #666; width: 50px; display: inline-block; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Code Coverage Report</h1>
        <h2>Repository: {self.repo_name}</h2>
        <div class="summary">
            <strong>Overall Coverage: {coverage_data['coverage_percentage']:.1f}%</strong>
            ({coverage_data['covered_lines']}/{coverage_data['total_lines']} lines)
        </div>
    </div>
"""
        
        for file_data in coverage_data['files']:
            coverage_class = 'coverage-low'
            if file_data['coverage_percentage'] >= 85:
                coverage_class = 'coverage-high'
            elif file_data['coverage_percentage'] >= 50:
                coverage_class = 'coverage-medium'
            
            html += f"""
    <div class="file {coverage_class}">
        <h3>{file_data['name']}</h3>
        <p>Coverage: {file_data['coverage_percentage']:.1f}% ({file_data['covered_lines']}/{file_data['total_lines']} lines)</p>
        <div class="code">
"""
            
            for line_data in file_data['lines'][:50]:  # Limit to first 50 lines for demo
                line_class = 'line-covered' if line_data['count'].isdigit() and int(line_data['count']) > 0 else 'line-uncovered'
                html += f"""<div class="line {line_class}"><span class="line-number">{line_data['number']:3d}:</span> {line_data['count']:>6} | {line_data['source']}</div>\n"""
            
            if len(file_data['lines']) > 50:
                html += f"<p><em>... and {len(file_data['lines']) - 50} more lines</em></p>"
            
            html += """        </div>
    </div>
"""
        
        html += """
</body>
</html>"""
        
        return html
    
    def clone_repository(self):
        """Clone the GitHub repository"""
        print(f"📥 Cloning repository: {self.repo_url}")
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp())
        repo_path = self.temp_dir / self.repo_name
        
        # Clone repository
        clone_cmd = ["git", "clone", self.repo_url, str(repo_path)]
        result = self._run_command(clone_cmd)
        
        if result is None or result.returncode != 0:
            print(f"❌ Failed to clone repository: {self.repo_url}")
            return None
        
        print(f"✅ Repository cloned to: {repo_path}")
        return repo_path
    
    def _cleanup(self):
        """Clean up temporary files and rollback modifications"""
        print("\n🧹 Cleaning up...")
        
        # Rollback LLM modifications
        if self.applied_modifications:
            print("  Rolling back temporary modifications...")
            self.llm_assistant.rollback_modifications(self.applied_modifications)
            self.applied_modifications = []
        
        # Remove temporary directory
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                print(f"  ✅ Removed temporary directory: {self.temp_dir}")
            except Exception as e:
                print(f"  ⚠️  Could not remove temporary directory: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Enhanced GitHub Repository Coverage Generator with LLM')
    parser.add_argument('repo_url', nargs='?', help='GitHub repository URL')
    parser.add_argument('--output-dir', default='coverage_output', help='Output directory for coverage report')
    parser.add_argument('--config', default='config.ini', help='Configuration file path')
    
    args = parser.parse_args()
    
    # Get repository URL from arguments or config
    repo_url = args.repo_url
    if not repo_url:
        config = configparser.ConfigParser()
        config.read(args.config)
        repo_url = config.get('DEFAULT', 'repository_url', fallback=None)
        
        if not repo_url:
            print("❌ No repository URL provided. Use:")
            print("  python generate_coverage.py <repo_url>")
            print("  or set repository_url in config.ini")
            return False
    
    # Create and run coverage generator
    generator = EnhancedCoverageGeneratorV2(repo_url, args.output_dir, args.config)
    success = generator.generate_coverage_report()
    
    if success:
        print("\n🎉 Coverage report generation completed successfully!")
        print(f"📄 Report available at: {generator.output_dir}/index.html")
        return True
    else:
        print("\n❌ Coverage report generation failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)