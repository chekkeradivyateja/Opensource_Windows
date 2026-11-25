# How the release bundle is built (for the trainer/maintainer)

Trainees do **not** need this page. It records how `oss_flow_windows_v0.1.0.zip` was made so it can be
rebuilt or updated.

## 1. Build PC

The build PC is a Windows PC with MSYS2 (UCRT64), which is used only as the build toolbox. Packages (exact versions are in
[TOOLS.md](TOOLS.md)):
```bash
pacman -S --needed mingw-w64-ucrt-x86_64-verilator mingw-w64-ucrt-x86_64-gcc make perl \
  mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-z3 lcov mingw-w64-ucrt-x86_64-lz4 \
  mingw-w64-ucrt-x86_64-iverilog mingw-w64-ucrt-x86_64-yosys vim
```
Before installing anything, check the package list with `pacman -S --print`. Pin versions; never update blindly.

## 2. Downloaded parts (check SHA-256)

| Part | URL | SHA-256 |
|---|---|---|
| UVM | `https://github.com/verilator/uvm/archive/656f20d087370a7c742e00188d20bbf30fa95339.tar.gz` | `fd28a1b0a789376dd83c3903f4f06cc38d4e5969f64062bea36da8e88c0c07b8` |
| Surfer | `https://gitlab.com/api/v4/projects/42073614/packages/generic/surfer/v0.7.0/surfer_win_v0.7.0.zip` | `4fbb0ad93e1aa958f6944c036a8d01b36b267a96e7f904683317235cd041fc24` |
| Graphviz | `https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/16.1.2/windows_10_cmake_Release_Graphviz-16.1.2-win64.zip` | `0924501672e796e05d3b6dd402d518e352ed28e9329dc668f40ce52357aa9f4b` |
| gvim | `https://github.com/vim/vim-win32-installer/releases/download/v9.2.1398/gvim_9.2.1398_x64.zip` | `0161b9deb47f10c788e9965e1b2ca96604a2b0aed9e68b99c562ba806d8f3566` |

UVM patch: see [TOOLS.md](TOOLS.md#uvm-patch-windows-and-verilator). After applying it, check that undoing the
rename gives back the original file's SHA-256.

## 3. Bundle layout

```
oss_flow_bundle\
  usr\  ucrt64\  etc\  tmp\  var\tmp\   copy of the MSYS2 folders, trimmed (see below)
  opt\uvm\  opt\surfer\  opt\graphviz\  opt\gvim\
  launcher\oss_flow.py   OSS_Flow.cmd   Verification_Terminal.cmd
  templates\  examples\  docs\  licenses\  VERSIONS.txt
```
The bundle also contains:
- `usr\bin\vi`, a script: `exec /usr/bin/vim "$@"`
- `usr\bin\gvim`, a script: `exec /opt/gvim/vim/vim92/gvim.exe "$@"`. gvim's own folder is not on PATH,
  because it contains its own `tee.exe`/`diff.exe`.

Left out when copying (with robocopy `/XD` and `/XF`):
- `usr\share\{man,info,doc,locale}`
- `ucrt64\share\{man,info,doc,locale}`
- `ucrt64\lib\python3.14\test`
- `ucrt64\lib\ghdl`
- `ucrt64\lib\gcc\x86_64-w64-mingw32\16.2.0\{adalib,adainclude}`
- `var\` (the pacman database)
- files `pacman*`, `makepkg*`, `repo-*`, `libLLVM*.dll`, `gnat*`, `ghdl*`, `verilator_bin_dbg.exe`

## 4. Start scripts

`Verification_Terminal.cmd` sets these for its own window only:
- `PATH` = `opt\surfer; opt\graphviz\bin; ucrt64\bin; usr\bin; System32`
- `MSYSTEM=UCRT64`, `CHERE_INVOKING=1`, `MSYS2_PATH_TYPE=inherit`
- `UVM_HOME=<bundle>/opt/uvm/src`
- `HOME=%USERPROFILE%`

It then starts `usr\bin\bash.exe --login`. `.cmd` files must have CRLF line endings, and Makefiles must have
LF line endings with real TABs. `.gitattributes` enforces this.

## 5. Test before every release

1. Unzip the new ZIP to a new folder and run everything through its `Verification_Terminal.cmd`:
   - design: `make report`
   - SV: `make regress covhtml` + FST waves
   - basic: `make regress covtxt synth`
   - UVM: `make regress covhtml`
2. Run the launcher self-test with the bundle's Python:
   `ucrt64\bin\python3.exe launcher\oss_flow.py --selftest <new empty folder> --uvm`.
   It must print `SELFTEST PASSED`.
3. Check the windows on screen: launcher, gvim, Surfer, schematic, FSM diagram, coverage reports.
4. Update [TESTED.md](TESTED.md) with real results only.

## 6. Make the ZIP

```powershell
cd D:\
tar.exe -a -c -f oss_flow_windows_vX.Y.Z.zip --exclude "oss_flow_bundle/tmp/gvim_not_shipped" oss_flow_bundle
(Get-FileHash oss_flow_windows_vX.Y.Z.zip -Algorithm SHA256).Hash.ToLower()
```
Upload the ZIP and its `.sha256` file to a GitHub **Release**. They must never go into git: GitHub refuses
files over 100 MB in a repository, while Release files may be up to 2 GB.
