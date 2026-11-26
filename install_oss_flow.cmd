@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem ==========================================================================
rem  install_oss_flow.cmd : one-click installer for the OSS Flow tools
rem  (open-source Verilog design + verification flow, Windows 10/11 64-bit)
rem
rem  Double-click = install. No admin rights needed. Nothing is installed into
rem  Windows itself: the tools go into one folder, plus 4 shortcuts.
rem
rem  Options (from a terminal):
rem    --check          check this PC only; changes nothing
rem    --zip FILE       install from a local copy of the ZIP (offline / USB)
rem    --dir PATH       install folder (default C:\oss_flow_bundle; no spaces)
rem    --uninstall      remove the shortcuts and move the tools folder to a
rem                     backup name (your projects are never touched)
rem ==========================================================================

rem ----- release settings: the only lines to change for a new release -----
set "VERSION=v0.2.0"
set "ZIP_NAME=oss_flow_windows_v0.2.0.zip"
set "DOWNLOAD_BASE=https://github.com/chekkeradivyateja/Opensource_Windows/releases/download/v0.2.0"
set "ZIP_SHA256=e245caf6f9ae9b49cc04cca982b25198d5fe8b0305904643734a523c6b3eea46"
set "DEFAULT_DIR=C:\oss_flow_bundle"
set "MIN_FREE_GB=3"
set "MIN_BUILD=17134"
rem -------------------------------------------------------------------------
rem  Maintainer test hooks (environment variables, never needed by trainees):
rem  OSSFLOW_TEST_ARCH, OSSFLOW_TEST_BUILD, OSSFLOW_TEST_FREE_GB,
rem  OSSFLOW_TEST_SHA (wrong expected checksum), OSSFLOW_TEST_BREAK_EXTRACT,
rem  OSSFLOW_TEST_OFFLINE, OSSFLOW_NO_PAUSE, OSSFLOW_NO_SHORTCUTS
rem -------------------------------------------------------------------------
if defined OSSFLOW_TEST_SHA set "ZIP_SHA256=%OSSFLOW_TEST_SHA%"

set "MODE=install"
set "DIR=%DEFAULT_DIR%"
set "LOCALZIP="
:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--check"     (set "MODE=check"     & shift & goto parse_args)
if /i "%~1"=="--uninstall" (set "MODE=uninstall" & shift & goto parse_args)
if /i "%~1"=="--dir"       (set "DIR=%~2"        & shift & shift & goto parse_args)
if /i "%~1"=="--zip"       (set "LOCALZIP=%~f2"  & shift & shift & goto parse_args)
if /i "%~1"=="--help" goto usage
if /i "%~1"=="/?"     goto usage
echo Unknown option: %~1
goto usage
:args_done

for /f "usebackq delims=" %%t in (`powershell -NoProfile -NonInteractive -Command "Get-Date -Format yyyyMMdd_HHmmss"`) do set "STAMP=%%t"
if not defined STAMP set "STAMP=%RANDOM%%RANDOM%"
set "LOG=%TEMP%\oss_flow_install_%STAMP%.log"
> "%LOG%" echo OSS Flow installer %VERSION% log, %STAMP%

for %%I in ("%DIR%") do set "DIR=%%~fI"
if "%DIR:~-1%"=="\" set "DIR=%DIR:~0,-1%"
for %%I in ("%DIR%") do set "LEAF=%%~nxI"
set "DRIVE=%DIR:~0,1%"

call :say "============================================================"
call :say " OSS Flow installer %VERSION%  (Verilog design + verification)"
call :say "============================================================"
call :say "Install folder: %DIR%"
call :say "Log file:       %LOG%"

call :detect_existing
if "%MODE%"=="uninstall" goto do_uninstall

call :preflight
if "%MODE%"=="check" goto do_check_end
if %NFAIL% GTR 0 (
  call :say ""
  call :say "STOPPED: fix the FAIL items above, then run the installer again."
  call :say "Nothing was changed on this PC."
  goto end_fail
)
goto do_install

rem ======================================================================
:do_check_end
call :say ""
if %NFAIL% GTR 0 (call :say "RESULT: %NFAIL% FAIL, %NWARN% WARN. Fix the FAIL items before installing.") else (call :say "RESULT: ready to install (%NWARN% WARN). Nothing was changed.")
if %NFAIL% GTR 0 goto end_fail
goto end_ok

rem ======================================================================
:do_install
call :say ""
call :say "2. Existing installation"
if "%EXISTING%"=="foreign" (
  call :say "  FAIL  %DIR% already exists and is NOT an OSS Flow folder."
  call :say "        It was not touched. Choose another folder with --dir, or rename that folder yourself."
  goto end_fail
)
if "%EXISTING%"=="same" (
  call :say "  OSS Flow %VERSION% is already installed in %DIR%. Nothing to do."
  call :say "  To check it, double-click the desktop shortcut 'OSS Flow'."
  goto end_ok
)
set "BACKUP="
if "%EXISTING%"=="ours" (
  call :say "  Found an older or unknown OSS Flow version in %DIR%:"
  call :say "    !OLDVER!"
  call :say "  It will be MOVED to %DIR%_backup_%STAMP% (not deleted). Your projects are not affected."
  call :ask_yes "  Replace it with %VERSION%?"
  if errorlevel 1 (
    call :say "  You answered No. Nothing was changed."
    goto end_ok
  )
) else (
  call :say "  None found. A new installation will be made."
)

call :say ""
call :say "3. Getting the tools ZIP and checking it (before anything is changed)"
if defined LOCALZIP (
  set "ZIP=%LOCALZIP%"
  set "SRC=local file"
  call :say "  Using local file: !ZIP!"
) else (
  set "SRC=%DOWNLOAD_BASE%/%ZIP_NAME%"
  set "DLDIR=%TEMP%\oss_flow_download"
  if not exist "!DLDIR!\" mkdir "!DLDIR!"
  set "ZIP=!DLDIR!\%ZIP_NAME%"
  set "HAVE="
  if exist "!ZIP!" (
    call :hash "!ZIP!"
    if /i "!HASH!"=="%ZIP_SHA256%" set "HAVE=1"
  )
  if defined HAVE (
    call :say "  Already downloaded earlier and correct: !ZIP!"
  ) else (
    call :say "  Downloading %ZIP_NAME% (about 420 MB) from GitHub ..."
    curl.exe -L --fail --retry 3 --retry-delay 5 -o "!ZIP!.part" "%DOWNLOAD_BASE%/%ZIP_NAME%"
    if errorlevel 1 (
      call :say "  FAIL  Download failed. Check the internet connection and run again."
      call :say "        Offline: copy the ZIP from USB and run:  install_oss_flow.cmd --zip <path to ZIP>"
      call :say "        Nothing was changed."
      goto end_fail
    )
    move /y "!ZIP!.part" "!ZIP!" >nul
  )
  curl.exe -s -L --fail -o "!ZIP!.sha256" "%DOWNLOAD_BASE%/%ZIP_NAME%.sha256" >nul 2>>"%LOG%"
  if not errorlevel 1 (
    findstr /i /c:"%ZIP_SHA256%" "!ZIP!.sha256" >nul
    if errorlevel 1 (
      call :say "  FAIL  The checksum published on GitHub differs from the one in this installer."
      call :say "        Download the newest installer from the Releases page. Nothing was changed."
      goto end_fail
    )
  )
)
if not exist "!ZIP!" (
  call :say "  FAIL  ZIP not found: !ZIP!  Nothing was changed."
  goto end_fail
)
call :say "  Checking SHA-256 ..."
call :hash "!ZIP!"
if /i not "!HASH!"=="%ZIP_SHA256%" (
  call :say "  FAIL  SHA-256 does not match: the ZIP is damaged or not the right file."
  call :say "        expected %ZIP_SHA256%"
  call :say "        got      !HASH!"
  call :say "        Nothing was changed. Download the ZIP again."
  goto end_fail
)
call :say "  PASS  SHA-256 matches %ZIP_SHA256%"

call :say ""
call :say "4. Installing"
if "%EXISTING%"=="ours" (
  set "BACKUP=%DIR%_backup_%STAMP%"
  move "%DIR%" "!BACKUP!" >nul 2>>"%LOG%"
  if errorlevel 1 (
    set "BACKUP="
    call :say "  FAIL  Could not move the old folder. Close all OSS Flow windows, terminals,"
    call :say "        gvim and Surfer, then run again. Nothing was changed."
    goto end_fail
  )
  call :say "  Old version moved to !BACKUP!"
)
set "STAGE=%DIR%_new_%STAMP%"
mkdir "%STAGE%" 2>>"%LOG%"
if errorlevel 1 goto install_failed
call :say "  Unpacking about 35,000 files (1 to 5 minutes, please wait) ..."
if defined OSSFLOW_TEST_BREAK_EXTRACT (
  call :say "  TEST HOOK: simulating a broken unpack"
  goto install_failed
)
tar.exe -x -f "!ZIP!" -C "%STAGE%" 2>>"%LOG%"
if errorlevel 1 goto install_failed
if not exist "%STAGE%\oss_flow_bundle\Verification_Terminal.cmd" goto install_failed
move "%STAGE%\oss_flow_bundle" "%DIR%" >nul 2>>"%LOG%"
if errorlevel 1 goto install_failed
rmdir "%STAGE%" 2>nul
> "%DIR%\INSTALLED.txt" (
  echo OSS Flow %VERSION%
  echo zip: %ZIP_NAME%
  echo sha256: %ZIP_SHA256%
  echo installed: %STAMP%
  echo source: !SRC!
)
call :say "  PASS  Tools installed in %DIR%"

call :say ""
call :say "5. Shortcuts"
if defined OSSFLOW_NO_SHORTCUTS (
  call :say "  Skipped (test hook)."
) else (
  call "%DIR%\Make_Shortcuts.cmd" --quiet >>"%LOG%" 2>&1
  if errorlevel 1 (
    call :say "  WARN  Could not create shortcuts. Double-click this file to try again:"
    call :say "        %DIR%\Make_Shortcuts.cmd"
  ) else (
    call :say "  PASS  Desktop and Start menu: 'OSS Flow' and 'Verification Terminal'"
  )
)

call :say ""
call :say "6. Self-test (1 to 3 minutes)"
call :say "  Tool versions:"
call "%DIR%\Verification_Terminal.cmd" "cd /examples/design_seq_det/simdir && make --no-print-directory check" > "%TEMP%\oss_flow_versions_%STAMP%.txt" 2>&1
for /f "usebackq delims=" %%v in ("%TEMP%\oss_flow_versions_%STAMP%.txt") do (
  echo %%v | findstr /i /c:"Verilator" /c:"Icarus" /c:"Yosys" /c:"graphviz" /c:"surfer" >nul && call :say "    %%v"
)
set "ST=%TEMP%\oss_flow_selftest_%STAMP%.txt"
"%DIR%\ucrt64\bin\python3.exe" "%DIR%\launcher\oss_flow.py" --selftest "%DIR%\tmp\install_selftest_%STAMP%" > "!ST!" 2>&1
type "!ST!" >> "%LOG%"
findstr /c:"SELFTEST PASSED" "!ST!" >nul
if errorlevel 1 (
  set "SELFTEST=FAIL"
  call :say "  FAIL  Self-test failed. Failed checks:"
  for /f "usebackq delims=" %%l in (`findstr /c:"FAIL" "!ST!"`) do call :say "    %%l"
  call :say "  If you see 'blocked' or 'Access is denied', this PC's security policy blocks"
  call :say "  the tools: ask your IT team. Full details: %LOG%"
) else (
  set "SELFTEST=PASS"
  for /f "usebackq delims=" %%l in (`findstr /c:"SELFTEST PASSED" "!ST!"`) do call :say "  PASS  %%l"
)

call :say ""
call :say "============================================================"
if "!SELFTEST!"=="PASS" (call :say " DONE: OSS Flow %VERSION% is installed and working.") else (call :say " INSTALLED, BUT THE SELF-TEST FAILED (see above).")
call :say "============================================================"
call :say " Start:  desktop shortcut 'OSS Flow' (buttons) or 'Verification Terminal'."
call :say " Guide:  %DIR%\docs\TRAINEE_GUIDE.md"
if defined BACKUP call :say " Old version kept in !BACKUP! ; delete it when the new one works."
if not defined LOCALZIP call :say " The downloaded ZIP is kept in %TEMP%\oss_flow_download for offline installs; you may delete it."
call :say " Uninstall later:  install_oss_flow.cmd --uninstall"
if "!SELFTEST!"=="PASS" goto end_ok
goto end_fail

rem ----------------------------------------------------------------------
:install_failed
call :say "  FAIL  Installing failed. Details: %LOG%"
if exist "%DIR%\" (
  move "%DIR%" "%DIR%_failed_%STAMP%" >nul 2>>"%LOG%"
  call :say "        The unfinished install was moved to %DIR%_failed_%STAMP% ; you may delete it."
)
if exist "%STAGE%\" rmdir "%STAGE%" 2>nul
if exist "%STAGE%\" call :say "        Unfinished unpacked files are in %STAGE% ; you may delete that folder."
if defined BACKUP (
  move "!BACKUP!" "%DIR%" >nul 2>>"%LOG%"
  if errorlevel 1 (
    call :say "        Could not restore the old version automatically:"
    call :say "        rename !BACKUP! back to %DIR%"
  ) else (
    call :say "        Your previous installation was restored in %DIR%."
  )
)
goto end_fail

rem ======================================================================
:do_uninstall
call :say ""
if not "%EXISTING%"=="ours" if not "%EXISTING%"=="same" (
  call :say "No OSS Flow installation found in %DIR%. Nothing was changed."
  call :say "Use --dir PATH if you installed it somewhere else."
  goto end_ok
)
call :say "This will:"
call :say "  - remove the shortcuts 'OSS Flow' and 'Verification Terminal' (desktop and Start menu)"
call :say "  - MOVE %DIR% to %DIR%_removed_%STAMP%"
call :say "Your projects (for example %USERPROFILE%\vlsi_work) are NOT touched."
call :ask_yes "Uninstall OSS Flow?"
if errorlevel 1 (
  call :say "You answered No. Nothing was changed."
  goto end_ok
)
powershell -NoProfile -NonInteractive -Command "$d=[Environment]::GetFolderPath('Desktop'); $m=Join-Path ([Environment]::GetFolderPath('Programs')) 'OSS Flow'; foreach($f in @($d,$m)){ foreach($n in @('OSS Flow.lnk','Verification Terminal.lnk')){ $p=Join-Path $f $n; if(Test-Path -LiteralPath $p){ Remove-Item -LiteralPath $p } } }; if((Test-Path -LiteralPath $m) -and -not (Get-ChildItem -LiteralPath $m)){ Remove-Item -LiteralPath $m }" >>"%LOG%" 2>&1
call :say "  Shortcuts removed."
move "%DIR%" "%DIR%_removed_%STAMP%" >nul 2>>"%LOG%"
if errorlevel 1 (
  call :say "  FAIL  Could not move %DIR%. Close all OSS Flow windows, terminals, gvim and Surfer,"
  call :say "        then run the uninstall again."
  goto end_fail
)
call :say "  Tools folder moved to %DIR%_removed_%STAMP%"
call :say "  To free about 1.3 GB, delete that folder yourself when you are sure."
goto end_ok

rem ======================================================================
:detect_existing
set "EXISTING=none"
set "OLDVER="
if not exist "%DIR%\" exit /b 0
dir /a /b "%DIR%" 2>nul | findstr "^" >nul || exit /b 0
set "EXISTING=foreign"
if not exist "%DIR%\VERSIONS.txt" exit /b 0
findstr /c:"Open-source Verilog design + verification flow for Windows" "%DIR%\VERSIONS.txt" >nul || exit /b 0
set "EXISTING=ours"
set "OLDVER=no INSTALLED.txt (unzipped by hand or older version)"
if exist "%DIR%\INSTALLED.txt" (
  for /f "usebackq delims=" %%a in ("%DIR%\INSTALLED.txt") do if not defined OLDLINE set "OLDLINE=%%a"
  set "OLDVER=!OLDLINE!"
  findstr /i /c:"%ZIP_SHA256%" "%DIR%\INSTALLED.txt" >nul && set "EXISTING=same"
)
exit /b 0

rem ======================================================================
:preflight
set /a NFAIL=0, NWARN=0
call :say ""
call :say "1. Checking this PC"
set "ARCH=%PROCESSOR_ARCHITECTURE%"
if defined PROCESSOR_ARCHITEW6432 set "ARCH=%PROCESSOR_ARCHITEW6432%"
if defined OSSFLOW_TEST_ARCH set "ARCH=%OSSFLOW_TEST_ARCH%"
if /i "%ARCH%"=="AMD64" (call :pass "64-bit Windows on Intel/AMD [%ARCH%]") else (call :fail "This PC is %ARCH%; the tools need 64-bit Windows on Intel/AMD [x64]. Use another PC.")

set "BUILD="
for /f "usebackq delims=" %%b in (`powershell -NoProfile -NonInteractive -Command "[Environment]::OSVersion.Version.Build"`) do set "BUILD=%%b"
if defined OSSFLOW_TEST_BUILD set "BUILD=%OSSFLOW_TEST_BUILD%"
if not defined BUILD (
  call :fail "Could not read the Windows version [PowerShell missing?]"
) else if !BUILD! GEQ %MIN_BUILD% (
  call :pass "Windows build !BUILD!"
) else (
  call :fail "Windows build !BUILD! is too old. Update to Windows 10 version 1803 or newer."
)

set "RAM10="
for /f "usebackq delims=" %%m in (`powershell -NoProfile -NonInteractive -Command "[int]((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB*10)"`) do set "RAM10=%%m"
if not defined RAM10 (
  call :warn "Could not read the RAM size"
) else (
  set /a RAMGB=RAM10/10, RAMDEC=RAM10%%10
  if !RAM10! GEQ 70 (call :pass "RAM !RAMGB!.!RAMDEC! GB") else (call :warn "RAM !RAMGB!.!RAMDEC! GB: design and SV flows work; UVM builds need about 4 GB free [8 GB PC recommended]")
)

if not "%DIR%"=="%DIR: =%" (
  call :fail "Install folder has a space: %DIR%. Use a folder without spaces, e.g. --dir C:\oss_flow_bundle"
) else if "%LEAF%"=="" (
  call :fail "Install folder cannot be a drive root: %DIR%"
) else (
  call :pass "Install folder name is OK [no spaces]"
)

set "FREE="
for /f "usebackq delims=" %%f in (`powershell -NoProfile -NonInteractive -Command "[int]((Get-PSDrive -Name %DRIVE% -ErrorAction Stop).Free/1GB)"`) do set "FREE=%%f"
if defined OSSFLOW_TEST_FREE_GB set "FREE=%OSSFLOW_TEST_FREE_GB%"
if not defined FREE (
  call :fail "Drive %DRIVE%: not found"
) else if !FREE! GEQ %MIN_FREE_GB% (
  call :pass "Free space on %DRIVE%: !FREE! GB [need %MIN_FREE_GB% GB]"
) else (
  call :fail "Free space on %DRIVE%: only !FREE! GB; need %MIN_FREE_GB% GB. Free up space or use --dir on another drive."
)

set "MISSING="
for %%x in (curl.exe tar.exe powershell.exe) do (where %%x >nul 2>&1 || set "MISSING=!MISSING! %%x")
if defined MISSING (call :fail "Windows tools missing:!MISSING!. Windows 10 version 1803 or newer includes them.") else (call :pass "Windows tools curl, tar, PowerShell found")

if defined LOCALZIP (
  if exist "%LOCALZIP%" (call :pass "Local ZIP found: %LOCALZIP%") else (call :fail "Local ZIP not found: %LOCALZIP%")
) else (
  set "HTTP=000"
  if not defined OSSFLOW_TEST_OFFLINE for /f "usebackq delims=" %%c in (`curl.exe -s -o nul -I -L --max-time 30 -w "%%{http_code}" "%DOWNLOAD_BASE%/%ZIP_NAME%"`) do set "HTTP=%%c"
  if "!HTTP!"=="200" (call :pass "Download address reachable [GitHub Releases]") else (call :fail "Cannot reach GitHub [HTTP !HTTP!]. Check the internet, or install offline with --zip FILE.")
)

if "%EXISTING%"=="none" call :pass "No existing installation in %DIR%"
if "%EXISTING%"=="same" call :pass "OSS Flow %VERSION% is already installed in %DIR%"
if "%EXISTING%"=="ours" call :warn "An older OSS Flow is in %DIR%; it would be moved to a backup [you will be asked]"
if "%EXISTING%"=="foreign" call :fail "%DIR% exists and is not an OSS Flow folder; it will not be touched. Use --dir."

if not "%EXISTING%"=="none" if not "%EXISTING%"=="foreign" if exist "%DIR%\usr\bin\bash.exe" (
  "%DIR%\usr\bin\bash.exe" -c "exit 0" >nul 2>&1
  if errorlevel 1 (call :fail "Programs in %DIR% cannot run [blocked by a security policy?]. Ask your IT team.") else (call :pass "Programs in %DIR% can run")
)

set "OTHER="
for %%x in (verilator iverilog yosys) do (for /f "delims=" %%p in ('where %%x 2^>nul') do set "OTHER=!OTHER! %%p")
if defined OTHER call :say "  INFO  Other tool installs on PATH [not touched]:!OTHER!"
exit /b 0

rem ======================================================================
:hash
set "HASH="
for /f "usebackq delims=" %%h in (`powershell -NoProfile -NonInteractive -Command "(Get-FileHash -LiteralPath '%~1' -Algorithm SHA256).Hash.ToLower()"`) do set "HASH=%%h"
if not defined HASH for /f "skip=1 delims=" %%h in ('certutil -hashfile "%~1" SHA256 ^| findstr /v /c:"CertUtil"') do if not defined HASH set "HASH=%%h"
if defined HASH set "HASH=!HASH: =!"
exit /b 0

:ask_yes
set "ANS="
set /p "ANS=%~1 Type yes and press Enter (anything else = No): "
if /i "!ANS!"=="yes" exit /b 0
exit /b 1

:say
set "MSG=%~1"
if not defined MSG (echo.& >>"%LOG%" echo.& exit /b 0)
echo(!MSG!
>>"%LOG%" echo(!MSG!
exit /b 0

:pass
call :say "  PASS  %~1"
exit /b 0

:warn
set /a NWARN+=1
call :say "  WARN  %~1"
exit /b 0

:fail
set /a NFAIL+=1
call :say "  FAIL  %~1"
exit /b 0

:usage
echo.
echo Usage: install_oss_flow.cmd [--check] [--zip FILE] [--dir PATH] [--uninstall]
echo   (no option)   install OSS Flow %VERSION% into %DEFAULT_DIR%
echo   --check       check this PC only; changes nothing
echo   --zip FILE    install from a local ZIP (offline)
echo   --dir PATH    install into another folder (no spaces)
echo   --uninstall   remove shortcuts; move the tools folder to a backup name
exit /b 2

:end_ok
if not defined OSSFLOW_NO_PAUSE (echo.& pause)
exit /b 0

:end_fail
if not defined OSSFLOW_NO_PAUSE (echo.& pause)
exit /b 1
