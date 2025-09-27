# Coverage Generator Launcher Comparison

## 🆚 run_coverage.py vs run_coverage.bat

### Python Launcher (`run_coverage.py`) - **RECOMMENDED**

#### ✅ Advantages:
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Real-time Output**: Shows coverage generation progress in real-time
- **Better Error Handling**: Detailed error messages and graceful failure handling
- **Advanced Options**: 
  - `--no-browser`: Skip opening browser
  - `--output-dir`: Custom output directory
  - `--help`: Built-in help system
- **Professional Interface**: Clean banner and status indicators
- **UTF-8 Support**: Better handling of international characters
- **Virtual Environment Management**: Automated venv setup and activation
- **Exit Code Handling**: Proper return codes for automation
- **Exception Handling**: Comprehensive error catching and reporting

#### 🚀 Usage Examples:
```bash
# Basic usage
python run_coverage.py

# With custom repository
python run_coverage.py https://github.com/user/repo.git

# Don't open browser automatically
python run_coverage.py --no-browser

# Custom output directory
python run_coverage.py --output-dir my_reports

# Get help
python run_coverage.py --help
```

### Batch File (`run_coverage.bat`) - Legacy Support

#### ✅ Still Works:
- Basic Windows functionality maintained
- Simple command line interface
- Automatic browser opening

#### ⚠️ Limitations:
- Windows-only
- Limited error handling
- No advanced options
- Basic output formatting
- Encoding issues with special characters

## 🎯 Migration Guide

### From Batch to Python:
```bash
# Old way
run_coverage.bat

# New way
python run_coverage.py
```

```bash
# Old way with URL
run_coverage.bat https://github.com/user/repo.git

# New way with URL
python run_coverage.py https://github.com/user/repo.git
```

## 🛠️ Features Comparison

| Feature | run_coverage.py | run_coverage.bat |
|---------|-----------------|------------------|
| Cross-platform | ✅ | ❌ (Windows only) |
| Real-time output | ✅ | ❌ |
| Advanced options | ✅ | ❌ |
| Error handling | ✅ | ⚠️ Basic |
| UTF-8 support | ✅ | ❌ |
| Help system | ✅ | ❌ |
| Exit codes | ✅ | ⚠️ Basic |
| Professional UI | ✅ | ⚠️ Basic |

## 🚀 Recommendation

**Use `python run_coverage.py`** for the best experience. The batch file is kept for backward compatibility but the Python launcher provides a much better user experience with advanced features and cross-platform support.