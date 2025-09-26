@echo off
echo Opening Enhanced Coverage Report...
echo.

if exist "coverage_output_local\index.html" (
    echo Opening local test coverage report...
    start "" "coverage_output_local\index.html"
) else if exist "coverage_output\index.html" (
    echo Opening main coverage report...
    start "" "coverage_output\index.html"
) else (
    echo No coverage report found!
    echo Run one of these commands first:
    echo   run_coverage_v2.bat
    echo   python test_local.py
    echo   python demo.py
)

pause