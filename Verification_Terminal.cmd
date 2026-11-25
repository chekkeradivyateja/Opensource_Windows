@echo off
rem Opens a terminal with the open-source design + verification tools on PATH (this window only).
rem No system setting is changed. Usage:  Verification_Terminal.cmd            (interactive)
rem                                       Verification_Terminal.cmd "command"  (run one command)
setlocal
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "MSYSTEM=UCRT64"
set "CHERE_INVOKING=1"
set "MSYS2_PATH_TYPE=inherit"
set "PATH=%ROOT%\opt\surfer;%ROOT%\opt\graphviz\bin;%ROOT%\ucrt64\bin;%ROOT%\usr\bin;%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\WindowsPowerShell\v1.0"
set "UVM_HOME=%ROOT:\=/%/opt/uvm/src"
if not defined HOME set "HOME=%USERPROFILE%"
if "%~1"=="" (
  "%ROOT%\usr\bin\bash.exe" --login -i
) else (
  "%ROOT%\usr\bin\bash.exe" --login -c "%~1"
)
exit /b %ERRORLEVEL%
