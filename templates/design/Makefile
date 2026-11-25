# =============================================================================
#  Verilog DESIGN flow for Windows (MSYS2 UCRT64 terminal)
#  sim (Icarus) -> waves (Surfer) -> lint (Verilator) -> synth (Yosys)
#  -> schematic (Yosys + Graphviz) -> FSM diagram (Yosys + Graphviz) -> one report
#  Start here:  make help
# =============================================================================
#  Layout:  <project>/rtl/*.v   <project>/tb/*.v   <project>/simdir/Makefile (this file)
#  Rule: each module lives in a file named after it (alu.v holds "module alu"),
#  because the tools find submodules by file name (extra unused files are allowed).
#  The testbench must call $dumpfile("dump.vcd") and $dumpvars, and print
#  "PASS: all checks passed" only when all of its own checks pass.
# =============================================================================

# ============================== EDIT HERE ====================================
# 1. Top design module and top testbench module
TOP     ?= seq_det
TB_TOP  ?= seq_det_tb
# 2. Source folders (relative to this simdir/ folder)
RTL_DIR ?= ../rtl
TB_DIR  ?= ../tb
# 3. FSM diagram: encodings of the state(s) where the Moore output is 1, drawn as
#    double circles (names as shown in the diagram, e.g. 100). Several: DETECT = 100 011
#    Leave empty if the design has no FSM: 'make report' then skips the FSM step.
DETECT  ?= 100
# 4. Windows programs (give the full path if one is not on PATH)
SURFER  ?= surfer.exe
DOT     ?= dot.exe
# =============================================================================

SHELL       := /bin/bash
.SHELLFLAGS := -o pipefail -c
# Open a file with its Windows default program (browser for .svg, editor for .txt)
OPEN     = cmd //c start "" "$$(cygpath -w $(1))"
# Used only so make rebuilds the SVG files when any RTL file changes
DEPS    := $(wildcard $(RTL_DIR)/*.v)
# Yosys: read only the top file, then pull in just the modules it instantiates
YS_READ  = read_verilog $(RTL_DIR)/$(TOP).v; hierarchy -check -top $(TOP) -libdir $(RTL_DIR)

.PHONY: help check all sim waves surfer gtkwave lint synth schematic fsm report \
        open_schematic open_synth_schematic open_fsm open_lint open_report clean

help:
	@echo "make sim                  - Icarus simulation -> sim_report.txt, dump.vcd"
	@echo "make waves                - run sim, then open dump.vcd in Surfer"
	@echo "make gtkwave              - same, in GTKWave (if installed)"
	@echo "make lint                 - Verilator -Wall lint of the RTL -> lint_report.txt"
	@echo "make synth                - Yosys synthesis -> synth_report.txt, synth_stat.txt, synth_out.v"
	@echo "make schematic            - SVG schematics: $(TOP)_rtl.svg and $(TOP)_synth.svg"
	@echo "make fsm                  - FSM state diagram: $(TOP)_fsm.svg (needs an FSM; set DETECT)"
	@echo "make all                  - sim + lint + synth + schematic"
	@echo "make report               - run everything, write ONE report: flow_report.txt"
	@echo "make open_schematic       - open $(TOP)_rtl.svg      (open_synth_schematic: $(TOP)_synth.svg)"
	@echo "make open_fsm             - draw the FSM diagram and open it"
	@echo "make open_lint            - run lint and open lint_report.txt"
	@echo "make open_report          - run everything and open flow_report.txt"
	@echo "make check                - show tool versions"
	@echo "make clean                - delete only the files this Makefile creates"
	@echo "Settings: TOP=$(TOP) TB_TOP=$(TB_TOP) DETECT=\"$(DETECT)\""

check:
	@verilator --version
	@iverilog -V 2>&1 | head -1
	@yosys -V
	@"$(DOT)" -V 2>&1 | head -1
	@command -v "$(SURFER)" >/dev/null && "$(SURFER)" --version || echo "surfer: MISSING ($(SURFER))"

all: sim lint synth schematic

# -s: simulate only the testbench top; -y: find modules by file name; -Y .v: file suffix
sim:
	iverilog -g2012 -s $(TB_TOP) -y $(RTL_DIR) -y $(TB_DIR) -Y .v -o sim.out $(TB_DIR)/$(TB_TOP).v
	vvp -n sim.out | tee sim_report.txt
	@grep -q "PASS: all checks passed" sim_report.txt || { echo "SIMULATION FAILED (see sim_report.txt)"; exit 1; }

waves surfer: sim
	"$(SURFER)" dump.vcd

gtkwave: sim
	@command -v gtkwave >/dev/null || { echo "GTKWave is not installed; use 'make waves' (Surfer)"; exit 1; }
	gtkwave dump.vcd

# Keeps Verilator's real exit code: make stops when lint finds warnings or errors
lint:
	@verilator --lint-only -Wall --top-module $(TOP) -y $(RTL_DIR) $(RTL_DIR)/$(TOP).v > lint_report.txt 2>&1; rc=$$?; \
	if [ $$rc -eq 0 ]; then echo "Lint passed: no warnings or errors" >> lint_report.txt; \
	else echo "Lint FAILED: warnings/errors found (verilator exit $$rc)" >> lint_report.txt; fi; \
	cat lint_report.txt; exit $$rc

synth:
	yosys -q -l synth_report.txt -p "$(YS_READ); synth -top $(TOP); tee -o synth_stat.txt stat; write_verilog -noattr synth_out.v"
	@cat synth_stat.txt

# Yosys writes .dot (module name last: show draws only that module), Graphviz draws the SVG
$(TOP)_rtl.svg: $(DEPS)
	yosys -q -p "$(YS_READ); prep -top $(TOP); show -format dot -prefix $(TOP)_rtl $(TOP)"
	"$(DOT)" -Tsvg $(TOP)_rtl.dot -o $@

$(TOP)_synth.svg: $(DEPS)
	yosys -q -p "$(YS_READ); synth -top $(TOP); show -format dot -prefix $(TOP)_synth $(TOP)"
	"$(DOT)" -Tsvg $(TOP)_synth.dot -o $@

schematic: $(TOP)_rtl.svg $(TOP)_synth.svg
	@echo "Created $(TOP)_rtl.svg and $(TOP)_synth.svg"

# State diagram: Yosys extracts the FSM, awk turns the transition table into a graph,
# Graphviz draws it. Arrows show the input bit; DETECT states are double circles.
fsm:
	@if [ -f $(TOP).kiss2 ]; then mv -f $(TOP).kiss2 $(TOP).kiss2.old; fi
	yosys -q -l fsm_report.txt -p "$(YS_READ); proc; opt_expr; opt_clean; fsm_detect; fsm_extract; fsm_opt; fsm_info; fsm_export -origenc -o $(TOP).kiss2"
	@test -s $(TOP).kiss2 || { echo "No FSM found in $(TOP) (see fsm_report.txt)"; exit 1; }
	@( echo "digraph fsm {"; echo "  rankdir=LR;"; \
	  awk -v det="$(DETECT)" 'BEGIN{n=split(det,d," ");for(i=1;i<=n;i++)D[d[i]]=1} /^\./{next} NF==4{print "  \"" $$2 "\" -> \"" $$3 "\" [label=\"" $$1 "\"];"; S[$$2]; S[$$3]} END{for(k in S) print "  \"" k "\" [shape=" ((k in D)?"doublecircle":"circle") "];"}' $(TOP).kiss2; \
	  echo "}" ) > $(TOP)_fsm.dot
	"$(DOT)" -Tsvg $(TOP)_fsm.dot -o $(TOP)_fsm.svg
	@echo "Created $(TOP)_fsm.svg ($$(grep -c '^[01-]' $(TOP).kiss2) transitions; details in fsm_report.txt)"

# Runs every step (also after a failure), then writes ONE report; exits 1 if any step FAILED
report:
	-@$(MAKE) --no-print-directory -k all $(if $(strip $(DETECT)),fsm) > flow_run.txt 2>&1
	@{ \
	echo "=================================================="; \
	echo " DESIGN FLOW REPORT  -  design: $(TOP)"; \
	echo " Generated: $$(date)"; \
	echo "=================================================="; \
	echo; echo "SUMMARY"; echo "-------"; \
	if grep -q "PASS: all checks passed" sim_report.txt 2>/dev/null; then echo "Simulation  : PASSED (all testbench checks passed)"; else echo "Simulation  : FAILED - see sim_report.txt"; fi; \
	if grep -q "Lint passed" lint_report.txt 2>/dev/null; then echo "Lint        : PASSED (no warnings or errors)"; else echo "Lint        : FAILED - see lint_report.txt"; fi; \
	if grep -q "End of script" synth_report.txt 2>/dev/null; then echo "Synthesis   : completed"; else echo "Synthesis   : FAILED - see synth_report.txt"; fi; \
	if [ -s $(TOP)_rtl.svg ] && [ -s $(TOP)_synth.svg ]; then echo "Schematic   : created"; else echo "Schematic   : FAILED - see flow_run.txt"; fi; \
	if [ -z "$(strip $(DETECT))" ]; then echo "FSM diagram : skipped (DETECT is empty)"; \
	elif [ -s $(TOP)_fsm.svg ]; then echo "FSM diagram : created"; else echo "FSM diagram : FAILED - see fsm_report.txt"; fi; \
	echo; echo "1. TOOL VERSIONS"; echo "----------------"; \
	echo "Verilator      : $$(verilator --version 2>&1 | head -1)"; \
	echo "Icarus Verilog : $$(iverilog -V 2>&1 | head -1)"; \
	echo "Yosys          : $$(yosys -V 2>&1 | head -1)"; \
	echo "Graphviz (dot) : $$("$(DOT)" -V 2>&1 | head -1)"; \
	echo; echo "2. LINT REPORT (Verilator)"; echo "--------------------------"; cat lint_report.txt 2>/dev/null; \
	echo; echo "3. SIMULATION (Icarus Verilog, last lines)"; echo "------------------------------------------"; tail -5 sim_report.txt 2>/dev/null; \
	echo "Waveform file: dump.vcd (open with: make waves)"; \
	echo; echo "4. SYNTHESIS STATISTICS (Yosys)"; echo "-------------------------------"; cat synth_stat.txt 2>/dev/null; \
	echo "Full synthesis log: synth_report.txt"; \
	echo; echo "5. GENERATED FILES"; echo "------------------"; \
	for f in sim_report.txt dump.vcd lint_report.txt synth_report.txt synth_out.v $(TOP)_rtl.svg $(TOP)_synth.svg $(TOP)_fsm.svg; do \
	  if [ -f "$$f" ]; then echo "  [x] $$f"; else echo "  [ ] $$f (missing)"; fi; \
	done; \
	} > flow_report.txt
	@cat flow_report.txt
	@echo; echo "Report saved to flow_report.txt"
	@! grep -q "FAILED" flow_report.txt

open_schematic: $(TOP)_rtl.svg
	$(call OPEN,$(TOP)_rtl.svg)

open_synth_schematic: $(TOP)_synth.svg
	$(call OPEN,$(TOP)_synth.svg)

open_fsm: fsm
	$(call OPEN,$(TOP)_fsm.svg)

open_lint:
	-@$(MAKE) --no-print-directory lint
	$(call OPEN,lint_report.txt)

open_report:
	-@$(MAKE) --no-print-directory report
	$(call OPEN,flow_report.txt)

# Deletes only files this Makefile creates; your sources are not touched.
clean:
	rm -f sim.out dump.vcd sim_report.txt lint_report.txt synth_report.txt synth_stat.txt synth_out.v \
	  $(TOP)_rtl.dot $(TOP)_rtl.svg $(TOP)_synth.dot $(TOP)_synth.svg \
	  fsm_report.txt $(TOP).kiss2 $(TOP).kiss2.old $(TOP)_fsm.dot $(TOP)_fsm.svg flow_run.txt flow_report.txt
