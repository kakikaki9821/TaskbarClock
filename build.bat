@echo off
echo === TaskbarClock Build ===
echo.

echo [1/3] Installing dependencies...
pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :error

echo.
echo [2/3] Running tests...
pytest tests/unit/ -v --tb=short
if errorlevel 1 goto :error

echo.
echo [3/3] Building exe...
pyinstaller --onefile --windowed --name=TaskbarClock --icon=resources/icon.ico --add-data "resources;resources" app.py
if errorlevel 1 goto :error

echo.
echo === Build complete! ===
echo Output: dist\TaskbarClock.exe
goto :end

:error
echo.
echo === Build FAILED ===
exit /b 1

:end
