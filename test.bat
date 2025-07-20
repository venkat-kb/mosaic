@echo off
echo Multi-Language Grievance System - Test Runner
echo =============================================
echo.

if "%1"=="demo" (
    echo Running language processing demo...
    python test_demo.py --demo
    goto end
)

if "%1"=="translation" (
    echo Testing translation functionality...
    python input.py --test-translation
    goto end
)

if "%1"=="processing" (
    echo Testing grievance processing...
    python input.py --test-processing
    goto end
)

if "%1"=="all" (
    echo Running all tests...
    python input.py --test-all
    goto end
)

if "%1"=="full" (
    echo Starting full system with speech recognition...
    echo Make sure your microphone is connected!
    python input.py
    goto end
)

echo Usage:
echo   test.bat demo        - Run language demo
echo   test.bat translation - Test translation only
echo   test.bat processing  - Test processing only
echo   test.bat all         - Run all tests
echo   test.bat full        - Run full system with speech
echo.
echo Example: test.bat demo

:end
pause
