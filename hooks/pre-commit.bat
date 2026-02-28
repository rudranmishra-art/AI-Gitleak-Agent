@echo off
echo Running AI-Gitleak-Agent...
python main.py
if errorlevel 1 (
    echo Commit blocked due to security policy.
    exit /b 1
)
echo Commit allowed.
exit /b 0
