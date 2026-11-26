@echo off
rem Make_Shortcuts.cmd : creates or updates the shortcuts 'OSS Flow' and 'Verification Terminal'
rem on the desktop and in the Start menu (folder 'OSS Flow'), with their icons.
rem The shortcuts start the real programs (pythonw.exe, cmd.exe), so Windows lets you pin them to
rem the taskbar: right-click the shortcut, Show more options, Pin to taskbar.
rem Usage: double-click it, or  Make_Shortcuts.cmd --quiet  (no "press a key" at the end).
setlocal
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
powershell -NoProfile -NonInteractive -Command "$q=[char]34; $r='%ROOT%'; $s=New-Object -ComObject WScript.Shell; $d=[Environment]::GetFolderPath('Desktop'); $m=Join-Path ([Environment]::GetFolderPath('Programs')) 'OSS Flow'; New-Item -ItemType Directory -Force -Path $m | Out-Null; $c=Join-Path $env:SystemRoot 'System32\cmd.exe'; $list=@(@('OSS Flow',($r+'\ucrt64\bin\pythonw.exe'),($q+$r+'\launcher\oss_flow.py'+$q),($r+'\launcher\oss_flow.ico'),'OSS Flow: design and verification (buttons)'),@('Verification Terminal',$c,('/c '+$q+$r+'\Verification_Terminal.cmd'+$q),($r+'\launcher\oss_terminal.ico'),'OSS Flow Terminal: bash with all the tools')); foreach($p in $list){ foreach($f in @($d,$m)){ $l=$s.CreateShortcut((Join-Path $f ($p[0]+'.lnk'))); $l.TargetPath=$p[1]; $l.Arguments=$p[2]; $l.IconLocation=$p[3]+',0'; $l.Description=$p[4]; $l.WorkingDirectory=$env:USERPROFILE; $l.Save() } }"
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" (
  echo Shortcuts 'OSS Flow' and 'Verification Terminal' are on the desktop and in the Start menu.
  echo To pin one to the taskbar: right-click it, Show more options, Pin to taskbar.
) else (
  echo Could not create the shortcuts [exit %RC%].
)
if /i not "%~1"=="--quiet" pause
exit /b %RC%
