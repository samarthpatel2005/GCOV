#!/usr/bin/env python3
"""
LLM Coverage Assistant using AWS Bedrock
Helps make repositories Gcov-compatible using AI
"""

import json
import boto3
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import configparser
from dotenv import load_dotenv


class LLMCoverageAssistant:
    def __init__(self, config_path="config.ini", env_path=".env"):
        # Load environment variables from .env file
        load_dotenv(env_path)
        
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        # AWS Bedrock configuration
        self.region = self.config.get('AWS_BEDROCK', 'region', fallback='us-east-1')
        self.model_id = self.config.get('AWS_BEDROCK', 'model_id', fallback='anthropic.claude-3-haiku-20240307-v1:0')
        self.max_tokens = self.config.getint('AWS_BEDROCK', 'max_tokens', fallback=4000)
        self.temperature = self.config.getfloat('AWS_BEDROCK', 'temperature', fallback=0.1)
        
        # Get AWS credentials from multiple sources in priority order:
        # 1. Environment variables (from .env file or system environment)
        # 2. Config file (fallback)
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID') or self.config.get('AWS_BEDROCK', 'aws_access_key_id', fallback=None)
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY') or self.config.get('AWS_BEDROCK', 'aws_secret_access_key', fallback=None)
        aws_region = os.getenv('AWS_DEFAULT_REGION') or self.region
        
        # Initialize Bedrock client with flexible credential handling
        try:
            # If credentials are available from environment or config, use them
            if aws_access_key and aws_secret_key:
                credential_source = ".env file" if os.getenv('AWS_ACCESS_KEY_ID') else "config.ini"
                print(f"Using AWS credentials from {credential_source}")
                self.bedrock_client = boto3.client(
                    'bedrock-runtime', 
                    region_name=aws_region,
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key
                )
            else:
                # Otherwise, use default credential chain (AWS CLI, IAM roles)
                print(f"Using AWS default credential chain (AWS CLI, IAM role, or other sources)")
                self.bedrock_client = boto3.client('bedrock-runtime', region_name=aws_region)
            
            print(f"SUCCESS: AWS Bedrock client initialized for region {aws_region}")
            
        except Exception as e:
            print(f"Warning: Could not initialize AWS Bedrock client: {e}")
            print("LLM features will use fallback mode")
            self.bedrock_client = None
    
    def analyze_repository_structure(self, repo_path: Path) -> Dict:
        """Analyze repository structure to understand project type and build system"""
        analysis = {
            'project_type': 'unknown',
            'build_system': 'unknown',
            'languages': [],
            'source_files': [],
            'build_files': [],
            'test_files': [],
            'has_makefile': False,
            'has_cmake': False,
            'has_tests': False,
            'gcov_compatibility': 'unknown'
        }
        
        # Scan for different file types
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                file_name = file_path.name.lower()
                file_suffix = file_path.suffix.lower()
                
                # Build system files
                if file_name in ['makefile', 'makefile.am']:
                    analysis['has_makefile'] = True
                    analysis['build_files'].append(str(file_path.relative_to(repo_path)))
                elif file_name == 'cmakelists.txt':
                    analysis['has_cmake'] = True
                    analysis['build_files'].append(str(file_path.relative_to(repo_path)))
                elif file_name in ['configure.ac', 'configure.in', 'autoconf', 'autotools']:
                    analysis['build_files'].append(str(file_path.relative_to(repo_path)))
                
                # Source files
                elif file_suffix in ['.c', '.cpp', '.cc', '.cxx', '.c++']:
                    analysis['source_files'].append(str(file_path.relative_to(repo_path)))
                    if 'c' not in analysis['languages']:
                        analysis['languages'].append('c' if file_suffix == '.c' else 'c++')
                
                # Test files
                elif 'test' in file_name or file_path.parent.name.lower() in ['test', 'tests']:
                    analysis['test_files'].append(str(file_path.relative_to(repo_path)))
                    analysis['has_tests'] = True
        
        # Determine project type
        if analysis['languages']:
            analysis['project_type'] = '/'.join(analysis['languages'])
        
        # Determine build system
        if analysis['has_cmake']:
            analysis['build_system'] = 'cmake'
        elif analysis['has_makefile']:
            analysis['build_system'] = 'make'
        elif analysis['source_files'] and not analysis['build_files']:
            analysis['build_system'] = 'simple'  # Simple source files without build system
        
        return analysis
    
    def check_gcov_compatibility(self, repo_path: Path, analysis: Dict) -> Tuple[bool, List[str]]:
        """Check if repository is already Gcov-compatible"""
        compatibility_issues = []
        
        # Check if Makefile already has coverage flags
        if analysis['has_makefile']:
            makefile_path = None
            for build_file in analysis['build_files']:
                if 'makefile' in build_file.lower():
                    makefile_path = repo_path / build_file
                    break
            
            if makefile_path and makefile_path.exists():
                content = makefile_path.read_text(encoding='utf-8', errors='ignore')
                if '-fprofile-arcs' not in content or '-ftest-coverage' not in content:
                    compatibility_issues.append("Makefile missing Gcov coverage flags")
                if '-lgcov' not in content:
                    compatibility_issues.append("Makefile missing Gcov linking flags")
        
        # Check for CMake coverage setup
        if analysis['has_cmake']:
            cmake_files = [repo_path / f for f in analysis['build_files'] if 'cmake' in f.lower()]
            for cmake_file in cmake_files:
                if cmake_file.exists():
                    content = cmake_file.read_text(encoding='utf-8', errors='ignore')
                    if 'coverage' not in content.lower() and 'gcov' not in content.lower():
                        compatibility_issues.append("CMakeLists.txt missing coverage configuration")
        
        # Check if tests exist
        if not analysis['has_tests']:
            compatibility_issues.append("No test files found")
        
        # Check for simple projects without build system
        if analysis['build_system'] == 'simple' and len(analysis['source_files']) > 1:
            compatibility_issues.append("Multiple source files without build system")
        
        is_compatible = len(compatibility_issues) == 0
        return is_compatible, compatibility_issues
    
    def generate_gcov_modifications(self, repo_path: Path, analysis: Dict, issues: List[str]) -> Dict:
        """Use LLM to generate modifications to make repository Gcov-compatible"""
        if not self.bedrock_client:
            return self._generate_fallback_modifications(analysis, issues)
        
        # Prepare context for LLM
        context = {
            'project_type': analysis['project_type'],
            'build_system': analysis['build_system'],
            'source_files': analysis['source_files'][:10],  # Limit to avoid token overflow
            'build_files': analysis['build_files'],
            'compatibility_issues': issues,
            'has_tests': analysis['has_tests']
        }
        
        # Read relevant build files content
        build_files_content = {}
        for build_file in analysis['build_files'][:3]:  # Limit to first 3 build files
            file_path = repo_path / build_file
            if file_path.exists() and file_path.stat().st_size < 10000:  # Limit file size
                try:
                    build_files_content[build_file] = file_path.read_text(encoding='utf-8', errors='ignore')
                except:
                    pass
        
        prompt = self._create_gcov_prompt(context, build_files_content)
        
        try:
            response = self._call_bedrock(prompt)
            return self._parse_llm_response(response)
        except Exception as e:
            print(f"LLM call failed: {e}")
            return self._generate_fallback_modifications(analysis, issues)
    
    def _create_gcov_prompt(self, context: Dict, build_files_content: Dict) -> str:
        """Create prompt for LLM to generate Gcov modifications"""
        prompt = f"""You are a C/C++ build system expert. Help make this repository compatible with Gcov code coverage.

Repository Analysis:
- Project Type: {context['project_type']}
- Build System: {context['build_system']}
- Source Files: {', '.join(context['source_files'])}
- Has Tests: {context['has_tests']}

Compatibility Issues Found:
{chr(10).join(f"- {issue}" for issue in context['compatibility_issues'])}

Current Build Files:
"""
        
        for file_name, content in build_files_content.items():
            prompt += f"\n=== {file_name} ===\n{content[:1000]}...\n"
        
        prompt += """

Please provide SPECIFIC modifications to make this repository Gcov-compatible:

1. MAKEFILE_CHANGES: Exact lines to add/modify in Makefile (if applicable)
2. CMAKE_CHANGES: Exact lines to add/modify in CMakeLists.txt (if applicable) 
3. TEST_COMPILATION: How to compile tests with coverage
4. GCOV_COMMANDS: Exact commands to generate coverage data
5. MISSING_FILES: Any files that need to be created

Respond in JSON format:
{
    "modifications": {
        "makefile_changes": ["line1", "line2"],
        "cmake_changes": ["line1", "line2"],
        "test_compilation": "exact command",
        "gcov_commands": ["cmd1", "cmd2"],
        "missing_files": [{"path": "filename", "content": "file content"}]
    },
    "explanation": "Brief explanation of changes"
}"""
        
        return prompt
    
    def _call_bedrock(self, prompt: str) -> str:
        """Call AWS Bedrock with the prompt"""
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = self.bedrock_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM response into structured modifications"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback parsing
        return {
            "modifications": {
                "makefile_changes": [],
                "cmake_changes": [],
                "test_compilation": "",
                "gcov_commands": [],
                "missing_files": []
            },
            "explanation": "Could not parse LLM response"
        }
    
    def _generate_fallback_modifications(self, analysis: Dict, issues: List[str]) -> Dict:
        """Generate basic modifications without LLM"""
        modifications = {
            "makefile_changes": [],
            "cmake_changes": [],
            "test_compilation": "",
            "gcov_commands": ["gcov *.gcda", "gcov *.c *.cpp"],
            "missing_files": []
        }
        
        # Basic Makefile modifications
        if analysis['has_makefile'] or analysis['build_system'] == 'simple':
            modifications["makefile_changes"] = [
                "CFLAGS += -fprofile-arcs -ftest-coverage -g -O0",
                "CXXFLAGS += -fprofile-arcs -ftest-coverage -g -O0", 
                "LDFLAGS += -lgcov",
                "",
                "coverage:",
                "\t@echo 'Generating coverage report...'",
                "\tgcov *.gcda",
                "\tlcov --capture --directory . --output-file coverage.info",
                "\tgenhtml coverage.info --output-directory coverage_html"
            ]
        
        # Basic CMake modifications
        if analysis['has_cmake']:
            modifications["cmake_changes"] = [
                "# Add coverage flags",
                "set(CMAKE_CXX_FLAGS \"${CMAKE_CXX_FLAGS} -fprofile-arcs -ftest-coverage\")",
                "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -fprofile-arcs -ftest-coverage\")",
                "target_link_libraries(${TARGET_NAME} gcov)"
            ]
        
        return {
            "modifications": modifications,
            "explanation": "Basic Gcov compatibility modifications"
        }
    
    def apply_modifications_temporarily(self, repo_path: Path, modifications: Dict) -> List[Path]:
        """Apply modifications temporarily (returns list of modified files for rollback)"""
        modified_files = []
        
        try:
            mod_data = modifications.get("modifications", {})
            
            # Apply Makefile changes
            makefile_changes = mod_data.get("makefile_changes", [])
            if makefile_changes:
                makefile_path = repo_path / "Makefile"
                if makefile_path.exists():
                    # Backup original
                    backup_path = makefile_path.with_suffix('.bak')
                    makefile_path.rename(backup_path)
                    modified_files.append(backup_path)
                    
                    # Apply changes
                    original_content = backup_path.read_text(encoding='utf-8', errors='ignore')
                    new_content = original_content + "\n\n# Gcov Coverage Flags\n" + "\n".join(makefile_changes)
                    makefile_path.write_text(new_content, encoding='utf-8')
                elif not makefile_path.exists() and makefile_changes:
                    # Create new Makefile
                    makefile_content = "\n".join(makefile_changes)
                    makefile_path.write_text(makefile_content, encoding='utf-8')
                    modified_files.append(makefile_path)
            
            # Apply CMake changes
            cmake_changes = mod_data.get("cmake_changes", [])
            if cmake_changes:
                cmake_path = repo_path / "CMakeLists.txt"
                if cmake_path.exists():
                    backup_path = cmake_path.with_suffix('.bak')
                    cmake_path.rename(backup_path)
                    modified_files.append(backup_path)
                    
                    original_content = backup_path.read_text(encoding='utf-8', errors='ignore')
                    new_content = original_content + "\n\n# Gcov Coverage Configuration\n" + "\n".join(cmake_changes)
                    cmake_path.write_text(new_content, encoding='utf-8')
            
            # Create missing files
            missing_files = mod_data.get("missing_files", [])
            for file_info in missing_files:
                if isinstance(file_info, dict) and 'path' in file_info and 'content' in file_info:
                    file_path = repo_path / file_info['path']
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(file_info['content'], encoding='utf-8')
                    modified_files.append(file_path)
            
        except Exception as e:
            print(f"Error applying modifications: {e}")
        
        return modified_files
    
    def rollback_modifications(self, modified_files: List[Path]):
        """Rollback temporary modifications"""
        for file_path in modified_files:
            try:
                if file_path.suffix == '.bak':
                    # Restore from backup
                    original_path = file_path.with_suffix('')
                    if original_path.exists():
                        original_path.unlink()
                    file_path.rename(original_path)
                else:
                    # Remove created file
                    if file_path.exists():
                        file_path.unlink()
            except Exception as e:
                print(f"Error rolling back {file_path}: {e}")