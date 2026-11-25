@echo off
rem Starts the OSS Flow launcher window (buttons for the design and verification flow).
rem Uses only the tools inside this folder; nothing is installed or changed on the PC.
setlocal
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
start "" "%ROOT%\ucrt64\bin\pythonw.exe" "%ROOT%\launcher\oss_flow.py" %*
