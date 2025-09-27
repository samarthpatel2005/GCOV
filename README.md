# Enhanced GitHub Repository Coverage Generator v2.0

## 🚀 New Features

This enhanced version now supports **both Gcov-compatible and non-compatible repositories** using AWS Bedrock LLM integration!

### Key Enhancements:

1. **🤖 LLM-Assisted Coverage Generation**: Uses AWS Bedrock to automatically make non-compatible repositories work with Gcov
2. **🔍 Smart Compatibility Detection**: Automatically detects if a repository supports Gcov or needs assistance
3. **⚙️ Temporary Modifications**: Applies changes temporarily without committing them to the repository
4. **📊 Enhanced Analysis**: Deep repository structure analysis for better coverage generation
5. **🐍 Python Launcher**: Cross-platform Python launcher with advanced features and real-time output

## 🛠️ How It Works

### For Gcov-Compatible Repositories:
- ✅ Direct coverage generation (same as v1.0)
- ✅ Fast and reliable
- ✅ No modifications needed

### For Non-Compatible Repositories:
- 🤖 **LLM Analysis**: AWS Bedrock analyzes the repository structure
- 📝 **Smart Modifications**: AI generates necessary build file changes
- ⚙️ **Temporary Application**: Changes applied temporarily (not committed)
- 📊 **Coverage Generation**: Gcov coverage generated with modifications
- 🧹 **Automatic Rollback**: All changes are rolled back after report generation

## 📋 Setup Requirements

### Basic Requirements (same as v1.0):
- Python 3.7+
- Git
- GCC/MinGW (for C/C++ projects)

### New Requirements for LLM Integration:
- **AWS Account** with Bedrock access
- **AWS Credentials** configured (via AWS CLI, environment variables, or IAM role)
- **Bedrock Model Access**: Access to Claude models (or other supported models)

## ⚙️ Configuration

Edit `config.ini` to configure AWS Bedrock:

```ini
[AWS_BEDROCK]
# AWS Bedrock configuration for LLM-assisted coverage
region = us-east-1
model_id = anthropic.claude-3-haiku-20240307-v1:0
max_tokens = 4000
temperature = 0.1

# Fallback behavior for non-Gcov compatible repositories
enable_llm_assistance = true
auto_apply_suggestions = false
create_backup_before_changes = true
```

## 🚀 Usage

### Option 1: Python Launcher (Recommended)
```cmd
python run_coverage.py
```
or with specific repository:
```cmd
python run_coverage.py https://github.com/username/repository.git
```

Additional options:
```cmd
# Don't open browser automatically
python run_coverage.py --no-browser https://github.com/username/repository.git

# Custom output directory
python run_coverage.py --output-dir my_coverage https://github.com/username/repository.git
```

### Option 2: Batch File (Windows)
```cmd
run_coverage.bat
```
or with specific repository:
```cmd
run_coverage.bat https://github.com/username/repository.git
```

### Option 3: Python Direct
```cmd
python generate_coverage_v2.py https://github.com/username/repository.git
```

### Option 3: Demo Mode
```cmd
python demo.py
```

## 🔄 Workflow Examples

### Example 1: Gcov-Compatible Repository
```
1. 📥 Clone repository
2. 🔍 Analyze structure → ✅ Compatible
3. 🔨 Build with coverage flags
4. 🧪 Run tests
5. 📊 Generate coverage data
6. 📄 Create HTML report
```

### Example 2: Non-Compatible Repository
```
1. 📥 Clone repository
2. 🔍 Analyze structure → ❌ Not compatible
3. 🤖 LLM analyzes issues
4. 📝 Generate modifications (Makefile, CMake, etc.)
5. ⚙️ Apply changes temporarily
6. 🔨 Build with coverage
7. 🧪 Run tests
8. 📊 Generate coverage data
9. 📄 Create HTML report
10. 🧹 Rollback all changes
```

## 📊 LLM Capabilities

The AWS Bedrock integration can handle:

- **Makefile Generation**: Adding coverage flags to existing or new Makefiles
- **CMake Configuration**: Modifying CMakeLists.txt for coverage support
- **Build System Detection**: Understanding complex build systems
- **Test Discovery**: Finding and configuring test execution
- **Missing File Creation**: Generating required build files
- **Flag Optimization**: Choosing optimal compiler flags for different scenarios

## 🔧 AWS Bedrock Setup

### 1. AWS Account Setup
1. Create an AWS account if you don't have one
2. Enable Amazon Bedrock in your region
3. Request access to Claude models (if needed)

### 2. AWS Credentials
Choose one of these methods:

#### Method A: .env File (Recommended)
Create a `.env` file in the project root:
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

#### Method B: AWS CLI
```cmd
aws configure
```

#### Method C: Environment Variables
```cmd
set AWS_ACCESS_KEY_ID=your_access_key
set AWS_SECRET_ACCESS_KEY=your_secret_key
set AWS_DEFAULT_REGION=us-east-1
```

#### Method D: IAM Role (for EC2/ECS)
Attach appropriate IAM role with Bedrock permissions

### 3. Required Permissions
Your AWS credentials need these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        }
    ]
}
```

## 📁 File Structure

```
Enhanced Coverage Generator v2.0/
├── generate_coverage_v2.py          # New enhanced main script
├── llm_coverage_assistant.py        # LLM integration module
├── run_coverage_v2.bat             # Enhanced batch script
├── demo.py                         # Demo script
├── config.ini                      # Configuration (updated)
├── requirements.txt                # Updated dependencies
├── generate_coverage_original.py   # Original v1.0 (backup)
└── README_v2.md                    # This file
```

## 🎯 Success Indicators

### Gcov-Compatible Repository:
```
✅ Repository is Gcov-compatible!
🔨 Building project with coverage instrumentation...
✅ Successfully compiled
🧪 Running tests and generating coverage data...
📄 Custom HTML report generated
✅ Coverage report generation completed successfully!
```

### Non-Compatible Repository:
```
⚠️  Repository is NOT Gcov-compatible
Issues found:
  - Makefile missing Gcov coverage flags
  - No test files found
🤖 Using LLM to make repository Gcov-compatible...
📝 LLM Generated Modifications:
  Explanation: Added Gcov flags and test compilation
⚙️  Applying temporary modifications...
🔨 Building with coverage (after modifications)...
✅ Successfully generated coverage report with LLM assistance!
📄 Note: Modifications were applied temporarily and will be rolled back
```

## 🚨 Troubleshooting

### Common Issues:

1. **AWS Credentials Error**
   ```
   Solution: Configure AWS credentials properly
   ```

2. **Bedrock Access Denied**
   ```
   Solution: Request access to Claude models in AWS Bedrock console
   ```

3. **LLM Generation Failed**
   ```
   Solution: System automatically falls back to basic modifications
   ```

4. **Build Still Fails After LLM**
   ```
   Solution: Repository may need manual intervention or specialized build setup
   ```

## 🔄 Fallback Behavior

If LLM integration fails:
- ✅ System automatically generates basic Gcov modifications
- ✅ Uses predefined templates for common scenarios
- ✅ Still attempts coverage generation
- ✅ Graceful degradation to v1.0 behavior

## 💡 Tips for Best Results

1. **Repository Selection**: Works best with C/C++ repositories that have clear build systems
2. **AWS Region**: Use regions where Bedrock is available (us-east-1, us-west-2, etc.)
3. **Model Choice**: Claude models work well for build system analysis
4. **Timeout Settings**: Large repositories may need longer processing time

## 🔮 Future Enhancements

- Support for more programming languages
- Integration with other LLM providers
- Advanced coverage report formatting
- Repository-specific optimization patterns
- Batch processing for multiple repositories

---

**Happy Coverage Testing! 🎉**