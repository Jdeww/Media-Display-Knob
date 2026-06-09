@echo off
echo Setting up Media Display Server...

set PROJECT_DIR=%~dp0
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set BAT_FILE=%STARTUP%\Server.bat

echo @echo off                                              > "%BAT_FILE%"
echo cd "%PROJECT_DIR%"                                    >> "%BAT_FILE%"
echo "%PROJECT_DIR%Media\Scripts\pythonw.exe" Server.py   >> "%BAT_FILE%"

echo.
echo Server startup script created at:
echo %BAT_FILE%
echo.
echo Starting server now...
start "" "%BAT_FILE%"
echo Done. The server will start automatically on every login.
pause
