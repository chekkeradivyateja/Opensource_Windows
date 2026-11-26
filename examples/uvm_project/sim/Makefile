# =============================================================================
#  Makefile for a UVM project with Verilator 5.054 and the patched Verilator UVM library
#  WINDOWS version (MSYS2 UCRT64 terminal). Based on the Ubuntu 24.04 template.
#  Windows changes: UVM built with +define+UVM_NO_DPI (no --vpi, no uvm_dpi.cc),
#  C++ built with -O1, CRLF fix before genhtml, Windows browser open, SURFER setting.
#  Start here:   make help
# =============================================================================
#  Expected project layout (change the paths in "EDIT HERE" if yours differ):
#    <project>/rtl/   design files (*.sv, *.v)
#    <project>/sva/   assertion modules + bind statements (optional)
#    <project>/tb/    *_if.sv interfaces, *_pkg.sv UVM package(s), top module
#    <project>/sim/   this Makefile; all outputs are written here
#  UVM_HOME is set by install.py in ~/.bashrc (open a new terminal after installing).
#  The test must print "TEST PASSED" in report_phase when it passes
#  (see alu_base_test in examples/uvm_project/tb/alu_pkg.sv).
#  The top module must call $dumpfile/$dumpvars when +WAVES is given.
#  NOTE (Windows): every build compiles the UVM library again: about 3 minutes and
#  about 3.6 GB RAM per compile job (measured on one PC; no ccache).
# =============================================================================

# ============================== EDIT HERE ====================================
# 1. Top module (the module that calls run_test())
TOP       := tb_top
# 2. Top design module (used by 'make lint' with -Wall and by 'make synth')
RTL_TOP   := alu
# 3. Source directories (relative to this sim/ folder)
RTL_DIR   := ../rtl
SVA_DIR   := ../sva
TB_DIR    := ../tb
# 4. Source files in compile order: interfaces, then packages, then the top module.
#    Default: tb/*_if.sv, then tb/*_pkg.sv, then the other tb/*.sv files.
#    If one package imports another, list them yourself in the right order, e.g.
#    TB_FILES := $(TB_DIR)/my_if.sv $(TB_DIR)/agent_pkg.sv $(TB_DIR)/env_pkg.sv $(TB_DIR)/tb_top.sv
RTL_FILES := $(wildcard $(RTL_DIR)/*.sv $(RTL_DIR)/*.v)
SVA_FILES := $(wildcard $(SVA_DIR)/*.sv)
TB_IFS    := $(wildcard $(TB_DIR)/*_if.sv)
TB_PKGS   := $(wildcard $(TB_DIR)/*_pkg.sv)
TB_FILES  := $(TB_IFS) $(TB_PKGS) $(filter-out $(TB_IFS) $(TB_PKGS),$(wildcard $(TB_DIR)/*.sv))
# 5. Include folders (for `include) and defines (NAME or NAME=VALUE), space separated
INC_DIRS  := $(RTL_DIR) $(SVA_DIR) $(TB_DIR)
DEFINES   :=
# 6. UVM test classes run by 'make regress' (each is passed as +UVM_TESTNAME=<name>)
TESTS     := alu_smoke_test alu_random_test
# 7. Time unit/precision for files that have no `timescale line
TIMESCALE := 1ns/1ps
# =============================================================================

# Options you can give on the command line, e.g.
#   make run TEST=alu_random_test SEED=7 WAVES=1 VERBOSITY=UVM_HIGH
TEST      ?= $(firstword $(TESTS))
SEED      ?= 1
WAVES     ?= 0
WAVE_FMT  ?= vcd
VERBOSITY ?= UVM_MEDIUM
PLUSARGS  ?=
# parallel C++ compile jobs; each job can need up to about 3 GB RAM with UVM
JOBS      ?= 1
# Windows: Surfer program (full path if surfer.exe is not on PATH)
SURFER    ?= surfer.exe

# ----------------------------- internals -------------------------------------
# Windows: the default -Os fails to link with MSYS2 GCC 16.2.0, so build the C++ with -O1
WIN_OPT  := -MAKEFLAGS "OPT_FAST=-O1 OPT_SLOW=-O1 OPT_GLOBAL=-O1"
SHELL       := /bin/bash
.SHELLFLAGS := -o pipefail -c
ifeq ($(UVM_HOME),)
  $(error UVM_HOME is not set. Open a new terminal after install.py, or: export UVM_HOME=<uvm>/src)
endif
# Windows: Verilator is a native program; give it a Windows-style path (C:/...)
UVM_HOME := $(shell cygpath -m "$(UVM_HOME)")
UVM_SRCS := $(UVM_HOME)/uvm_pkg.sv
SRCS     := $(RTL_FILES) $(SVA_FILES) $(TB_FILES)
VINC     := +incdir+$(UVM_HOME) $(addprefix +incdir+,$(INC_DIRS))
# Windows: UVM's C part (uvm_dpi.cc) does not link with MSYS2, so UVM runs without DPI
VDEF     := +define+UVM_NO_DPI $(addprefix +define+,$(DEFINES)) --timescale $(TIMESCALE)
TRACE    := $(if $(filter fst,$(WAVE_FMT)),--trace-fst,--trace)
SIM      := obj_dir/V$(TOP)
WAVEFILE := waves_$(TEST).$(WAVE_FMT)
COV_OFF  := uvm_cov_off.vlt
RUNARGS  := +UVM_TESTNAME=$(TEST) +UVM_VERBOSITY=$(VERBOSITY) +UVM_NO_RELNOTES \
            +verilator+seed+$(SEED) +verilator+coverage+file+cov/$(TEST).dat \
            $(if $(filter 1,$(WAVES)),+WAVES +WAVE_FILE=$(WAVEFILE)) $(PLUSARGS)
PASS_CHK := grep -q "TEST PASSED" logs/$$t.log && grep -q "UVM_ERROR :    0" logs/$$t.log \
            && grep -q "UVM_FATAL :    0" logs/$$t.log && ! grep -q "%Error" logs/$$t.log

.PHONY: help check lint lint_tb build sim run regress cov covhtml covopen waves gtkwave synth clean

help:
	@echo "Targets:"
	@echo "  make check                 show tool versions, UVM_HOME and the source files found"
	@echo "  make lint                  lint RTL+SVA with -Wall (fast)"
	@echo "  make lint_tb               lint the whole UVM testbench (about 10 s)"
	@echo "  make sim TEST=<name>       simulate only: run the last compile again (no compile)"
	@echo "  make build                 compile (first time 3-4 min; only recompiles on changes)"
	@echo "  make run TEST=<test>       run one UVM test -> logs/<test>.log, cov/<test>.dat"
	@echo "      options: SEED=<n> WAVES=1 WAVE_FMT=vcd|fst VERBOSITY=UVM_LOW|UVM_MEDIUM|UVM_HIGH"
	@echo "               PLUSARGS=\"+N=500\""
	@echo "  make regress               run all tests in TESTS, print PASS/FAIL table"
	@echo "  make cov                   merge coverage -> cov_report.txt, cov_annot/, cov_covergroup/"
	@echo "  make covhtml               HTML line-coverage report -> cov_html/index.html"
	@echo "  make covopen               open the HTML coverage report in the browser"
	@echo "  make waves TEST=<test>     open waves_<test>.vcd/.fst in Surfer (run with WAVES=1 first)"
	@echo "  make gtkwave TEST=<test>   same, in GTKWave"
	@echo "  make synth                 Yosys synthesis of RTL_TOP -> synth.log"
	@echo "  make clean                 delete all generated files"
	@echo "Current settings: TOP=$(TOP) RTL_TOP=$(RTL_TOP) TEST=$(TEST) SEED=$(SEED) JOBS=$(JOBS)"
	@echo "TESTS=\"$(TESTS)\""

check:
	@verilator --version
	@verilator_coverage --version | head -1
	@command -v genhtml >/dev/null && genhtml --version | head -1 || echo "genhtml (lcov): MISSING"
	@command -v yosys >/dev/null && yosys -V || echo "yosys: MISSING"
	@command -v "$(SURFER)" >/dev/null && "$(SURFER)" --version || echo "surfer: MISSING ($(SURFER))"
	@echo "UVM_HOME=$(UVM_HOME)"; test -f $(UVM_SRCS) && echo "UVM library: found" || echo "UVM library: MISSING"
	@echo "Source files in compile order:"; for f in $(SRCS); do echo "  $$f"; done

lint:
	verilator --lint-only -Wall $(addprefix +incdir+,$(INC_DIRS)) $(VDEF) --top-module $(RTL_TOP) \
	  $(RTL_FILES) $(SVA_FILES)
	@echo "LINT PASSED"

lint_tb:
	verilator --lint-only --timing -Wno-lint -Wno-style $(VINC) $(VDEF) --top-module $(TOP) \
	  $(UVM_SRCS) $(SRCS)
	@echo "LINT PASSED"

# The .vlt file switches coverage off for the UVM library, so reports show only your code.
$(COV_OFF):
	@printf '`verilator_config\ncoverage_off -file "%s/*"\n' "$(UVM_HOME)" > $@

build: $(COV_OFF)
	verilator --binary --assert --coverage $(TRACE) -Wno-fatal -Wno-lint -Wno-style -j $(JOBS) \
	  $(VINC) $(VDEF) --top-module $(TOP) $(WIN_OPT) $(COV_OFF) $(UVM_SRCS) $(SRCS)

# Compile + simulate. 'make build' = compile only, 'make sim' = simulate only (no compile).
run: build sim

sim:
	@test -e $(SIM).exe -o -e $(SIM) || { echo "Not compiled yet: run 'make build' (Compile) first"; exit 1; }
	@mkdir -p logs cov
	$(SIM) $(RUNARGS) 2>&1 | tee logs/$(TEST).log || true
	@t=$(TEST); if $(PASS_CHK); \
	  then echo "== $(TEST): PASS"; else echo "== $(TEST): FAIL (see logs/$(TEST).log)"; exit 1; fi

regress: build
	@fail=0; for t in $(TESTS); do \
	  $(MAKE) --no-print-directory run TEST=$$t >/dev/null 2>&1 || fail=1; \
	  if $(PASS_CHK); then printf "  %-24s PASS\n" $$t; \
	  else printf "  %-24s FAIL  (logs/%s.log)\n" $$t $$t; fi; \
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
	  cov_report.txt synth.log waves_*.vcd waves_*.fst $(COV_OFF)
