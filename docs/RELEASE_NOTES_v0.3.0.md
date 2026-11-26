# v0.3.0: pilot release 3 (Windows 10/11, 64-bit)

Same tools as v0.1.0 and v0.2.0. This release makes the OSS Flow window sharp on every screen, adds icons
and taskbar pinning, and gives the terminal a clear name. You still do not need Linux, WSL, MSYS2 or admin rights.

## Download

- `install_oss_flow.cmd`: one-click installer. It downloads the ZIP, checks it, installs to `C:\oss_flow_bundle`,
  creates the shortcuts and runs a self-test. An existing installation is moved aside first, not deleted.
- `oss_flow_windows_v0.3.0.zip`: all tools (about 1.3 GB after unzipping)
- `oss_flow_windows_v0.3.0.zip.sha256`: checksum. Compare it before unzipping by hand (see docs/INSTALL.md).

## What is new

- **Sharp window at any display scaling.** The OSS Flow window was blurry on screens set to 125 %, 150 % or
  175 % (most laptops). It now draws at the real screen resolution; sizes follow the scaling.
- **Icons**: OSS Flow (blue waveform) and Verification Terminal (black `>_`), on the window, the shortcuts and
  the taskbar.
- **Pin to taskbar**: the shortcuts now start the real programs, so right-click → Show more options → Pin to
  taskbar works. `Make_Shortcuts.cmd` creates or repairs both shortcuts; the installer uses it too.
- **Terminal**: window title **OSS Flow Terminal** and prompt `OSS Flow <folder>` instead of MSYS2's `UCRT64`.
  It is the bundle's own bash; MSYS2 is not needed.
- **Terminal here** button on the Single file tab (opens in the chosen file's folder).
- **Terminal cheat sheet** `docs/TERMINAL_CHEATSHEET.md`: every command for single files, design, SV and UVM
  projects on one page.

## Upgrading from v0.2.0

Run the new `install_oss_flow.cmd`. Your old folder is moved to a backup name; your projects in
`C:\Users\<you>\vlsi_work` are not touched. Unpin the old OSS Flow from the taskbar and pin the new shortcut.

## Tested

On the same Windows 11 PC with 7.7 GB RAM at 150 % display scaling: window check (both tabs, all result tabs,
nothing cut off), launcher self-test, shortcuts with icons and taskbar pin (checked on screen), the terminal
prompt, and the installer from the new ZIP. The details are in docs/TESTED.md.

## Known limits

- Pilot: not yet tested on other laptops, Windows 10, managed (Device Guard) PCs, or paths with spaces.
- Only 150 % display scaling was tested; on a second monitor with a different scaling the window may be soft.
- If Windows Terminal is the default console, a running terminal may appear under Windows Terminal on the
  taskbar instead of the pinned Verification Terminal icon.
- UVM runs without its C/DPI part, so there is no register backdoor and no regex in `uvm_config_db`.
- A UVM build takes 4–8 minutes and needs about 4 GB of free RAM.
- The programs are not digitally signed, so Windows SmartScreen may ask for confirmation.
- The Graphviz and Surfer licence texts are not yet included in the bundle (links are in licenses/README.md).
