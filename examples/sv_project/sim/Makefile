# =============================================================================
#  Makefile for a SystemVerilog project with Verilator (RTL + SVA + testbench)
#  WINDOWS version (MSYS2 UCRT64 terminal). Based on the Ubuntu 24.04 template.
#  Windows changes: C++ built with -O1, CRLF fix before genhtml, Windows browser open,
#  Surfer path is one setting (SURFER), GTKWave optional.
#  Start here:   make help
# =============================================================================
#  Expected project layout (change the paths in "EDIT HERE" if yours differ):
#    <project>/rtl/   design files (*.sv, *.v)
#    <project>/sva/   assertion modules + bind statements (optional)
#    <project>/tb/    testbench: packages (*_pkg.sv) and the top testbench
#    <project>/sim/   this Makefile; all outputs are written here
#  The testbench must read +TEST=<name> and print "TEST PASSED" or "TEST FAILED".
#  For waveforms the testbench must call $dumpfile/$dumpvars when +WAVES is given
#  (see examples/sv_project/tb/tb_top.sv).
# =============================================================================

# ============================== EDIT HERE ====================================
# 1. Top testbench module (the module nothing else instantiates)
TOP       := tb_top
# 2. Top design module (used by 'make lint' with -Wall and by 'make synth')
RTL_TOP   := alu
# 3. Source directories (relative to this sim/ folder)
RTL_DIR   := ../rtl
SVA_DIR   := ../sva
TB_DIR    := ../tb
# 4. Source files in compile order. Packages must come before files that import them.
#    Default: all files in each folder, and in tb/ the *_pkg.sv files first.
#    To set the order yourself, list the files, for example:
#    TB_FILES := $(TB_DIR)/my_pkg.sv $(TB_DIR)/my_if.sv $(TB_DIR)/tb_top.sv
RTL_FILES := $(wildcard $(RTL_DIR)/*.sv $(RTL_DIR)/*.v)
SVA_FILES := $(wildcard $(SVA_DIR)/*.sv)
TB_PKGS   := $(wildcard $(TB_DIR)/*_pkg.sv)
TB_FILES  := $(TB_PKGS) $(filter-out $(TB_PKGS),$(wildcard $(TB_DIR)/*.sv))
# 5. Include folders (for `include) and defines (NAME or NAME=VALUE), space separated
INC_DIRS  := $(RTL_DIR) $(SVA_DIR) $(TB_DIR)
DEFINES   :=
# 6. Tests run by 'make regress' (each is passed to the testbench as +TEST=<name>)
TESTS     := smoke random
# 7. Time unit/precision for files that have no `timescale line
TIMESCALE := 1ns/1ps
# =============================================================================

# Options you can give on the command line, e.g.  make run TEST=random SEED=7 WAVES=1
TEST      ?= $(firstword $(TESTS))
SEED      ?= 1
WAVES     ?= 0
WAVE_FMT  ?= vcd
PLUSARGS  ?=
JOBS      ?= 2
# Windows: Surfer program (full path if surfer.exe is not on PATH)
SURFER    ?= surfer.exe

# ----------------------------- internals -------------------------------------
# Windows: the default -Os fails to link with MSYS2 GCC 16.2.0, so build the C++ with -O1
WIN_OPT  := -MAKEFLAGS "OPT_FAST=-O1 OPT_SLOW=-O1 OPT_GLOBAL=-O1"
SHELL       := /bin/bash
.SHELLFLAGS := -o pipefail -c
SRCS     := $(RTL_FILES) $(SVA_FILES) $(TB_FILES)
VINC     := $(addprefix +incdir+,$(INC_DIRS))
VDEF     := $(addprefix +define+,$(DEFINES)) --timescale $(TIMESCALE)
TRACE    := $(if $(filter fst,$(WAVE_FMT)),--trace-fst,--trace)
SIM      := obj_dir/V$(TOP)
WAVEFILE := waves_$(TEST).$(WAVE_FMT)
RUNARGS  := +TEST=$(TEST) +verilator+seed+$(SEED) +verilator+coverage+file+cov/$(TEST).dat \
            $(if $(filter 1,$(WAVES)),+WAVES +WAVE_FILE=$(WAVEFILE)) $(PLUSARGS)

.PHONY: help check lint build sim run regress cov covhtml covopen waves gtkwave synth clean

help:
	@echo "Targets:"
	@echo "  make check                 show tool versions and the source files found"
	@echo "  make lint                  lint RTL+SVA with -Wall, then the whole testbench"
	@echo "  make sim TEST=<name>       simulate only: run the last compile again (no compile)"
	@echo "  make build                 compile (only recompiles when sources change)"
	@echo "  make run TEST=<name>       run one test -> logs/<name>.log, cov/<name>.dat"
	@echo "      options: SEED=<n> WAVES=1 WAVE_FMT=vcd|fst PLUSARGS=\"+N=500\""
	@echo "  make regress               run all tests in TESTS, print PASS/FAIL table"
	@echo "  make cov                   merge coverage -> cov_report.txt, cov_annot/, cov_covergroup/"
	@echo "  make covhtml               HTML line-coverage report -> cov_html/index.html"
	@echo "  make covopen               open the HTML coverage report in the browser"
	@echo "  make waves TEST=<name>     open waves_<name>.vcd/.fst in Surfer (run with WAVES=1 first)"
	@echo "  make gtkwave TEST=<name>   same, in GTKWave"
	@echo "  make synth                 Yosys synthesis of RTL_TOP -> synth.log"
	@echo "  make clean                 delete all generated files"
	@echo "Current settings: TOP=$(TOP) RTL_TOP=$(RTL_TOP) TESTS=\"$(TESTS)\" TEST=$(TEST) SEED=$(SEED)"

check:
	@verilator --version
	@verilator_coverage --version | head -1
	@command -v genhtml >/dev/null && genhtml --version | head -1 || echo "genhtml (lcov): MISSING"
	@command -v yosys >/dev/null && yosys -V || echo "yosys: MISSING"
	@command -v "$(SURFER)" >/dev/null && "$(SURFER)" --version || echo "surfer: MISSING ($(SURFER))"
	@echo "Source files in compile order:"; for f in $(SRCS); do echo "  $$f"; done

lint:
	verilator --lint-only -Wall $(VINC) $(VDEF) --top-module $(RTL_TOP) $(RTL_FILES) $(SVA_FILES)
	verilator --lint-only --timing $(VINC) $(VDEF) --top-module $(TOP) $(SRCS)
	@echo "LINT PASSED"

build:
	verilator --binary --assert --coverage $(TRACE) -Wno-fatal -j $(JOBS) $(VINC) $(VDEF) \
	  --top-module $(TOP) $(WIN_OPT) $(SRCS)

# Compile + simulate. 'make build' = compile only, 'make sim' = simulate only (no compile).
run: build sim

sim:
	@test -e $(SIM).exe -o -e $(SIM) || { echo "Not compiled yet: run 'make build' (Compile) first"; exit 1; }
	@mkdir -p logs cov
	$(SIM) $(RUNARGS) 2>&1 | tee logs/$(TEST).log || true
	@if grep -q "TEST PASSED" logs/$(TEST).log && ! grep -q "%Error" logs/$(TEST).log; \
	  then echo "== $(TEST): PASS"; else echo "== $(TEST): FAIL (see logs/$(TEST).log)"; exit 1; fi

regress: build
	@fail=0; for t in $(TESTS); do \
	  $(MAKE) --no-print-directory run TEST=$$t >/dev/null 2>&1 || fail=1; \
	  if grep -q "TEST PASSED" logs/$$t.log 2>/dev/null && ! grep -q "%Error" logs/$$t.log; \
	    then printf "  %-20s PASS\n" $$t; else printf "  %-20s FAIL  (logs/%s.log)\n" $$t $$t; fi; \
	done; \
	if [ $$fail = 0 ]; then echo "REGRESSION PASSED"; else echo "REGRESSION FAILED"; exit 1; fi

# Verilator's built-in std package (verilated_std.sv) is removed from the reports,
# so the numbers show only your design and testbench.
cov:
	@ls cov/*.dat >/dev/null 2>&1 || { echo "No coverage files in cov/. Run 'make run' or 'make regress' first."; exit 1; }
	verilator_coverage --write coverage_all.dat cov/*.dat
	grep -v verilated_std.sv coverage_all.dat > coverage.dat
	verilator_coverage --report summary,hier coverage.dat > cov_report.txt
	@sed -n '1,/^Hierarchy/p' cov_report.txt | head -n -1
	verilator_coverage --annotate cov_annot coverage.dat > /dev/null
	verilator_coverage --filter-type covergroup --annotate cov_covergroup --annotate-points coverage.dat > /dev/null
	@echo "Per-module and per-bin details: cov_report.txt | annotated sources: cov_annot/ | covergroup bins: cov_covergroup/"

covhtml: cov
	verilator_coverage --write-info coverage.info coverage.dat
	sed -i 's/\r$$//' coverage.info
	genhtml --quiet coverage.info --output-directory cov_html
	@echo "HTML report: cov_html/index.html  (open with: make covopen)"

covopen:
	cmd //c start "" "$$(cygpath -w cov_html/index.html)"

waves:
	"$(SURFER)" $(WAVEFILE)

gtkwave:
	@command -v gtkwave >/dev/null || { echo "GTKWave is not installed; use 'make waves' (Surfer)"; exit 1; }
	gtkwave $(WAVEFILE)

synth:
	yosys -p "read_verilog -sv $(RTL_FILES); synth -top $(RTL_TOP); stat" > synth.log
	@grep -A30 "Printing statistics" synth.log | tail -n +2
	@echo "Full log: synth.log"

# Deletes only files and folders this Makefile creates; your sources are not touched.
clean:
	rm -rf obj_dir logs cov cov_annot cov_covergroup cov_html coverage.dat coverage_all.dat coverage.info \
	  cov_report.txt synth.log waves_*.vcd waves_*.fst
