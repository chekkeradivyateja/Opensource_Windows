# System requirements

## Summary

| | Minimum | Recommended | Why |
|---|---|---|---|
| Operating system | Windows 10 or 11, **64-bit (x86-64)** | Windows 11 | the tools are 64-bit Windows programs |
| RAM | **8 GB** | 16 GB | a UVM build needs about **3.4–3.6 GB** at its peak |
| Free disk | **3 GB** + projects | 10 GB | see the table below |
| CPU | any 64-bit Intel or AMD | 4+ cores | UVM builds use 1 core (`JOBS=1`) to keep RAM low |
| Admin rights | not needed | | everything runs from one folder |
| Internet | once, to download | | works offline afterwards |
| Screen | 1366 × 768 | 1920 × 1080 | the OSS Flow window is about 980 × 760 |

**Not supported:** 32-bit Windows, Windows on ARM (for example Snapdragon laptops), Windows 7/8, macOS, and Linux
(Linux has its own flow: [OpenSource_Ubuntu_Ver](https://github.com/chekkeradivyateja/OpenSource_Ubuntu_Ver)).

To check your PC: press **Win + Pause** (or Settings → System → About) and look at *System type*
(must say *64-bit operating system, x64-based processor*) and *Installed RAM*.

## Measured on the test PC

| Item | Value |
|---|---|
| PC | Windows 11 Pro (build 26200), Intel Core 3 100U (6 cores), **7.7 GB RAM** |
| Release ZIP | see the Releases page |
| Unzipped tools | about **1.3 GB** (about 30,000 files) |
| Design flow (sim, lint, synth, schematic, FSM, report) | about **20 s** for the example |
| SV example: build + 2 tests | about **30 s** |
| UVM example: first build | **6–8 min**, peak RAM **3.4–3.6 GB** |
| UVM example: more tests with the same build | a few seconds each |
| Disk used by a UVM project after a build | about **0.9 GB** (`make clean` frees it) |
| Disk used by a design or SV project | a few MB |

UVM builds were about 30% slower from a folder under `C:\Users\...` than from `D:\` on the test PC.
Antivirus scanning is a likely reason but this was not checked.

## Before a UVM build

- Close big programs (browser tabs, video calls) so that about 4 GB of RAM is free.
- Keep `JOBS=1` (the default). More parallel jobs need about 3 GB **each**.

## Company or college laptops

Some managed PCs block new programs ("blocked by your organization's Device Guard policy", "This app has been
blocked by your system administrator"). The flow compiles a **new program for every simulation**, so such a policy
can stop it. You cannot fix this yourself. Ask your IT team to allow programs in the tools folder and your project
folder, or use another PC. Do not try to bypass the policy.
