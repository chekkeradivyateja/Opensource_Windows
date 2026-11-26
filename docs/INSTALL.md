# Installation (Windows 10/11, 64-bit)

The installation takes about **10 minutes**. No admin rights are needed, and nothing is changed in Windows settings.
You need about **3 GB** of free disk space.

There are two ways to install. **Way A (one-click installer)** is recommended. **Way B (manual)** does the same
steps by hand.

## Way A: one-click installer (recommended)

1. Download **`install_oss_flow.cmd`** from the
   [Releases](https://github.com/chekkeradivyateja/Opensource_Windows/releases) page, or from the repository:
   open the file, then click **Download raw file**.
2. **Double-click** `install_oss_flow.cmd`.
   - If Windows shows **"Windows protected your PC"**, click **More info → Run anyway**. The file is a plain text
     script; you can open it in Notepad and read it first.
3. A window shows each step:
   1. checks your PC
   2. downloads the tools (about 420 MB) and **checks the SHA-256**
   3. unpacks them to `C:\oss_flow_bundle`
   4. creates the shortcuts **OSS Flow** and **Verification Terminal** on the desktop and in the Start menu
      (with icons; right-click → Show more options → Pin to taskbar to pin them)
   5. runs a **self-test**

   It ends with `DONE: OSS Flow v0.2.0 is installed and working.`
4. Press a key to close the window, then start **OSS Flow** from the desktop.

**Options.** Open a Command Prompt in the folder that has the installer, then run one of these:

| Command | What it does |
|---|---|
| `install_oss_flow.cmd --check` | checks your PC only and changes nothing |
| `install_oss_flow.cmd --zip D:\oss_flow_windows_v0.2.0.zip` | **offline** install from a ZIP on a USB stick or shared drive |
| `install_oss_flow.cmd --dir D:\oss_flow_bundle` | installs to another folder (no spaces) |
| `install_oss_flow.cmd --uninstall` | removes the shortcuts and moves the tools folder to a backup name |

**What the installer never does:**
- It never deletes anything. An older version is **moved** to `..._backup_<date>`, but only after you type `yes`.
- It never touches your projects.
- It never changes Windows settings, never needs admin rights, and never installs a service.
- It downloads and checks everything **before** changing anything. If a step fails, the old version is restored.

If the installer reports a FAIL, it says what to do. The full log is in your Temp folder (the path is shown at the top).

## Way B: manual installation

### 1. Download

1. Go to <https://github.com/chekkeradivyateja/Opensource_Windows/releases>.
2. Under the newest release (**v0.2.0**), click these two files to download them:
   - `oss_flow_windows_v0.2.0.zip` (the tools)
   - `oss_flow_windows_v0.2.0.zip.sha256` (its checksum)

   They go to your **Downloads** folder.

**No internet on the lab PC?** Copy both files from a USB stick or a shared drive instead. Everything else is the same.

### 2. Check the download (do not skip)

This makes sure the file is complete and unchanged.

1. Open the **Downloads** folder. Click the address bar, type `powershell` and press **Enter**.
   A PowerShell window opens in that folder.
2. Type this command (or copy it) and press **Enter**:
   ```powershell
   (Get-FileHash .\oss_flow_windows_v0.2.0.zip -Algorithm SHA256).Hash
   ```
3. Open `oss_flow_windows_v0.2.0.zip.sha256` with Notepad. The long code in it must be **exactly the same** as
   the output of step 2 (capital or small letters do not matter).
   - **Same:** continue.
   - **Different:** delete the zip and download it again. If it is still different, report it (see README).

### 3. Unzip

1. Right-click `oss_flow_windows_v0.2.0.zip` and choose **Extract All...**.
2. As the destination, type `C:\` and click **Extract**. This takes a few minutes (about 30,000 files).
3. You now have the folder **`C:\oss_flow_bundle`**.

Rules for the location:
- **No spaces** in the path. `C:\oss_flow_bundle` is good, `C:\My Tools\...` is not.
- Keep it short and local (not on a network drive, not inside OneDrive).
- If you cannot write to `C:\`, use a folder in your user folder, for example
  `C:\Users\<you>\oss_flow_bundle`, as long as your user name has no spaces.

### 4. Shortcuts (optional)

Double-click `C:\oss_flow_bundle\Make_Shortcuts.cmd`. It creates **OSS Flow** (the window with buttons) and
**Verification Terminal** (commands) on the desktop and in the Start menu, with their icons.

**Pin to the taskbar:** right-click a shortcut → **Show more options** → **Pin to taskbar** (Windows 11), or
right-click → **Pin to taskbar** (Windows 10). The shortcuts start the real programs, so pinning works; a
shortcut made with *Send to → Desktop* on a `.cmd` file cannot be pinned.

## 5. First run check (both ways)

**Terminal check (2 minutes)**

Double-click `Verification_Terminal.cmd`. In the window that opens, type:
```bash
mkdir -p ~/vlsi_work && cd ~/vlsi_work
cp -r /examples/design_seq_det .
cd design_seq_det/simdir
make check
make report
```
- `make check` lists Verilator 5.054, Icarus 13.0, Yosys 0.66, Graphviz 16.1.2 and Surfer 0.7.0.
- `make report` ends with:
  ```
  Simulation  : PASSED (all testbench checks passed)
  Lint        : PASSED (no warnings or errors)
  Synthesis   : completed
  Schematic   : created
  FSM diagram : created
  ```

**Window check (1 minute)**

1. Double-click `OSS_Flow.cmd`.
2. Click **New project**, choose `sv_project`, and click **Create project**.
3. Click **Regression**. The output shows `smoke PASS`, `random PASS` and `REGRESSION PASSED` in green.
4. Click **Waveform**. If no waveform exists yet, tick **Save waveform**, click **Run test**, then **Waveform**.
   Surfer opens.

If both checks pass, the installation is complete. Continue with [TRAINEE_GUIDE.md](TRAINEE_GUIDE.md).

**Optional UVM check (6–8 minutes, needs about 4 GB of free RAM):** in the terminal, run
```bash
cd ~/vlsi_work && cp -r /examples/uvm_project . && cd uvm_project/sim && make regress
```
The result should be `alu_smoke_test PASS`, `alu_random_test PASS` and `REGRESSION PASSED`.

## 6. Where your work is saved

- `~` in the terminal is your Windows user folder (`C:\Users\<you>`).
- The examples are copied to `C:\Users\<you>\vlsi_work\...`. That is where you edit them.
- The tools folder `C:\oss_flow_bundle` is only read, never changed by the flow.

## 7. Update to a new version

- **Installer:** run the new `install_oss_flow.cmd`. It finds the old version, asks you, moves the old version to a
  backup, and installs the new one.
- **Manual:** rename the old folder (for example to `oss_flow_bundle_old`), then unzip the new ZIP.

Your projects in `vlsi_work` are not affected. Delete the old folder once the new one works.

## 8. Uninstall

- **Installer:** run `install_oss_flow.cmd --uninstall` and type `yes`. It removes the shortcuts and moves the
  tools folder to `C:\oss_flow_bundle_removed_<date>`. Delete that folder yourself to free about 1.3 GB.
- **Manual:** delete the folder `C:\oss_flow_bundle` and your shortcuts.

Your projects in `C:\Users\<you>\vlsi_work` stay either way; delete them too if you no longer need them. Nothing else
was installed.

## Problems?

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
