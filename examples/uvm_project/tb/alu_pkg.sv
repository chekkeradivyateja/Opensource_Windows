// alu_pkg.sv - UVM testbench for the alu: item, sequences, driver, monitor,
// scoreboard, coverage, agent, env and tests (compiled after uvm_pkg)
`timescale 1ns/1ps
package alu_pkg;
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  // ---------------- sequence item ----------------
  class alu_item extends uvm_sequence_item;
    rand bit [1:0] op;
    rand bit [7:0] a, b;
    bit      [8:0] result;     // filled in by the monitor
    constraint c_edges { a dist {0 := 1, 255 := 1, [1:254] :/ 8};
                         b dist {0 := 1, 255 := 1, [1:254] :/ 8}; }
    `uvm_object_utils(alu_item)
    function new(string name = "alu_item"); super.new(name); endfunction
    function string convert2string();
      return $sformatf("op=%0d a=%0d b=%0d result=%0d", op, a, b, result);
    endfunction
  endclass

  // ---------------- sequences ----------------
  class alu_smoke_seq extends uvm_sequence #(alu_item);
    `uvm_object_utils(alu_smoke_seq)
    function new(string name = "alu_smoke_seq"); super.new(name); endfunction
    task body();
      bit [1:0] ops[4] = '{0, 1, 2, 3};
      bit [7:0] as[4]  = '{200, 10, 8'hF0, 8'hFF};
      bit [7:0] bs[4]  = '{100, 20, 8'h3C, 8'h0F};
      for (int i = 0; i < 4; i++) begin
        req = alu_item::type_id::create("req");
        start_item(req);
        req.op = ops[i]; req.a = as[i]; req.b = bs[i];
        finish_item(req);
      end
    endtask
  endclass

  class alu_random_seq extends uvm_sequence #(alu_item);
    int unsigned n = 200;
    `uvm_object_utils(alu_random_seq)
    function new(string name = "alu_random_seq"); super.new(name); endfunction
    task body();
      repeat (n) begin
        req = alu_item::type_id::create("req");
        start_item(req);
        if (!req.randomize()) `uvm_fatal("RAND", "randomize failed")
        finish_item(req);
      end
    endtask
  endclass

  // ---------------- driver ----------------
  class alu_driver extends uvm_driver #(alu_item);
    virtual alu_if vif;
    `uvm_component_utils(alu_driver)
    function new(string name, uvm_component parent); super.new(name, parent); endfunction
    function void build_phase(uvm_phase phase);
      if (!uvm_config_db#(virtual alu_if)::get(this, "", "vif", vif))
        `uvm_fatal("NOVIF", "virtual interface not set")
    endfunction
    task run_phase(uvm_phase phase);
      vif.in_valid <= 0;
      @(posedge vif.clk iff vif.rst_n);
      forever begin
        seq_item_port.get_next_item(req);
        @(negedge vif.clk);
        vif.in_valid <= 1; vif.op <= req.op; vif.a <= req.a; vif.b <= req.b;
        @(negedge vif.clk);
        vif.in_valid <= 0;
        seq_item_port.item_done();
      end
    endtask
  endclass

  // ---------------- monitor ----------------
  class alu_monitor extends uvm_monitor;
    virtual alu_if vif;
    uvm_analysis_port #(alu_item) ap;
    `uvm_component_utils(alu_monitor)
    function new(string name, uvm_component parent); super.new(name, parent); endfunction
    function void build_phase(uvm_phase phase);
      ap = new("ap", this);
      if (!uvm_config_db#(virtual alu_if)::get(this, "", "vif", vif))
        `uvm_fatal("NOVIF", "virtual interface not set")
    endfunction
    task run_phase(uvm_phase phase);
      alu_item in_q[$];
      forever begin
        @(posedge vif.clk);
        if (vif.rst_n && vif.out_valid && in_q.size() > 0) begin
          alu_item t = in_q.pop_front();
          t.result = vif.result;
          ap.write(t);
        end
        if (vif.rst_n && vif.in_valid) begin
          alu_item t = alu_item::type_id::create("t");
          t.op = vif.op; t.a = vif.a; t.b = vif.b;
          in_q.push_back(t);
        end
      end
    endtask
  endclass

  // ---------------- scoreboard (reference model) ----------------
  class alu_scoreboard extends uvm_scoreboard;
    uvm_analysis_imp #(alu_item, alu_scoreboard) imp;
    int unsigned checked, errors;
    `uvm_component_utils(alu_scoreboard)
    function new(string name, uvm_component parent); super.new(name, parent); endfunction
    function void build_phase(uvm_phase phase); imp = new("imp", this); endfunction
    function void write(alu_item t);
      bit [8:0] exp;
      case (t.op)
        2'd0: exp = {1'b0, t.a} + {1'b0, t.b};
        2'd1: exp = {1'b0, t.a} - {1'b0, t.b};
        2'd2: exp = {1'b0, t.a & t.b};
        default: exp = {1'b0, t.a ^ t.b};
      endcase
      checked++;
      if (t.result !== exp) begin
        errors++;
        `uvm_error("SCB", $sformatf("MISMATCH %s expected=%0d", t.convert2string(), exp))
      end
    endfunction
    function void report_phase(uvm_phase phase);
      `uvm_info("SCB", $sformatf("checked=%0d errors=%0d", checked, errors), UVM_NONE)
    endfunction
  endclass

  // ---------------- functional coverage ----------------
  class alu_coverage extends uvm_subscriber #(alu_item);
    alu_item tr;
    `uvm_component_utils(alu_coverage)
    covergroup alu_cg;
      cp_op: coverpoint tr.op { bins add = {0}; bins sub = {1}; bins and_op = {2}; bins xor_op = {3}; }
      cp_a:  coverpoint tr.a  { bins zero = {0}; bins max = {255}; bins mid = {[1:254]}; }
      cp_b:  coverpoint tr.b  { bins zero = {0}; bins max = {255}; bins mid = {[1:254]}; }
      x_op_a: cross cp_op, cp_a;
    endgroup
    function new(string name, uvm_component parent);
      super.new(name, parent);
      alu_cg = new();
    endfunction
    function void write(alu_item t);
      tr = t;
      alu_cg.sample();
    endfunction
    function void report_phase(uvm_phase phase);
      `uvm_info("COV", $sformatf("functional coverage=%0.1f%%", alu_cg.get_coverage()), UVM_NONE)
    endfunction
  endclass

  // ---------------- agent and env ----------------
  class alu_agent extends uvm_agent;
    uvm_sequencer #(alu_item) sqr;
    alu_driver  drv;
    alu_monitor mon;
    `uvm_component_utils(alu_agent)
    function new(string name, uvm_component parent); super.new(name, parent); endfunction
    function void build_phase(uvm_phase phase);
      sqr = uvm_sequencer#(alu_item)::type_id::create("sqr", this);
      drv = alu_driver::type_id::create("drv", this);
      mon = alu_monitor::type_id::create("mon", this);
    endfunction
    function void connect_phase(uvm_phase phase);
      drv.seq_item_port.connect(sqr.seq_item_export);
    endfunction
  endclass

  class alu_env extends uvm_env;
    alu_agent      agt;
    alu_scoreboard scb;
    alu_coverage   cov;
    `uvm_component_utils(alu_env)
    function new(string name, uvm_component parent); super.new(name, parent); endfunction
    function void build_phase(uvm_phase phase);
      agt = alu_agent::type_id::create("agt", this);
      scb = alu_scoreboard::type_id::create("scb", this);
      cov = alu_coverage::type_id::create("cov", this);
    endfunction
    function void connect_phase(uvm_phase phase);
      agt.mon.ap.connect(scb.imp);
      agt.mon.ap.connect(cov.analysis_export);
    endfunction
  endclass

  // ---------------- tests (select with +UVM_TESTNAME=<name>) ----------------
  class alu_base_test extends uvm_test;
    alu_env env;
    `uvm_component_utils(alu_base_test)
    function new(string name, uvm_component parent); super.new(name, parent); endfunction
    function void build_phase(uvm_phase phase);
      env = alu_env::type_id::create("env", this);
    endfunction
    virtual task run_seq(); endtask
    task run_phase(uvm_phase phase);
      phase.raise_objection(this);
      run_seq();
      #50;                               // let the last results come out
      phase.drop_objection(this);
    endtask
    function void report_phase(uvm_phase phase);
      uvm_report_server rs = uvm_report_server::get_server();
      if (rs.get_severity_count(UVM_ERROR) == 0 && rs.get_severity_count(UVM_FATAL) == 0
          && env.scb.checked > 0)
        `uvm_info("RESULT", "TEST PASSED", UVM_NONE)
      else
        `uvm_info("RESULT", "TEST FAILED", UVM_NONE)
    endfunction
  endclass

  class alu_smoke_test extends alu_base_test;
    `uvm_component_utils(alu_smoke_test)
    function new(string name, uvm_component parent); super.new(name, parent); endfunction
    task run_seq();
      alu_smoke_seq seq = alu_smoke_seq::type_id::create("seq");
      seq.start(env.agt.sqr);
    endtask
  endclass

  class alu_random_test extends alu_base_test;
    `uvm_component_utils(alu_random_test)
    function new(string name, uvm_component parent); super.new(name, parent); endfunction
    task run_seq();
      alu_random_seq seq = alu_random_seq::type_id::create("seq");
      void'($value$plusargs("N=%d", seq.n));
      seq.start(env.agt.sqr);
    endtask
  endclass
endpackage
