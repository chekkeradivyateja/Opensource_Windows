// tb_top.sv - testbench for alu: constrained-random stimulus, covergroup, checker
// Tests (select with +TEST=<name>):  smoke  = each operation once with fixed values
//                                     random = +N=<count> random transactions (default 200)
// Waves: +WAVES writes waves.vcd (or waves.fst if built with FST tracing)
`timescale 1ns/1ps
module tb_top;
  import alu_tb_pkg::*;
  logic       clk;
  logic       rst_n;
  logic       in_valid;
  logic [1:0] op;
  logic [7:0] a, b;
  logic       out_valid;
  logic [8:0] result;
  int         errors, checked;

  alu dut (.*);

  initial clk = 0;
  always #5 clk = ~clk;   // 100 MHz

  // ---- functional coverage ----
  covergroup alu_cg @(posedge clk iff in_valid);
    cp_op: coverpoint op { bins add = {0}; bins sub = {1}; bins and_op = {2}; bins xor_op = {3}; }
    cp_a:  coverpoint a  { bins zero = {0}; bins max = {255}; bins mid = {[1:254]}; }
    cp_b:  coverpoint b  { bins zero = {0}; bins max = {255}; bins mid = {[1:254]}; }
    x_op_a: cross cp_op, cp_a;
  endgroup
  alu_cg cg = new();

  // ---- reference model + checker ----
  function automatic logic [8:0] model(logic [1:0] o, logic [7:0] x, logic [7:0] y);
    case (o)
      2'd0: return {1'b0, x} + {1'b0, y};
      2'd1: return {1'b0, x} - {1'b0, y};
      2'd2: return {1'b0, x & y};
      default: return {1'b0, x ^ y};
    endcase
  endfunction

  logic [8:0] expected;
  always @(posedge clk) begin
    if (!rst_n) begin checked <= 0; errors <= 0; end
    if (rst_n && in_valid) expected <= model(op, a, b);
    if (rst_n && out_valid) begin
      checked <= checked + 1;
      if (result !== expected) begin
        errors <= errors + 1;
        $error("result=%0d expected=%0d", result, expected);
      end
    end
  end

  task automatic drive(bit [1:0] o, bit [7:0] x, bit [7:0] y);
    @(negedge clk); in_valid = 1; op = o; a = x; b = y;
  endtask

  initial begin
    string test, wave_file;
    int n;
    alu_txn t;   // from alu_tb_pkg (randomized by Verilator using z3)
    if (!$value$plusargs("TEST=%s", test)) test = "smoke";
    if (!$value$plusargs("N=%d", n)) n = 200;
    if ($test$plusargs("WAVES")) begin
      if (!$value$plusargs("WAVE_FILE=%s", wave_file)) wave_file = "waves.vcd";
      $dumpfile(wave_file);
      $dumpvars(0, tb_top);
    end
    $display("TEST=%s", test);
    rst_n = 0; in_valid = 0; op = 0; a = 0; b = 0;
    repeat (3) @(negedge clk);
    rst_n = 1;
    case (test)
      "smoke": begin
        drive(0, 8'd200, 8'd100);   // ADD with carry
        drive(1, 8'd10,  8'd20);    // SUB with borrow
        drive(2, 8'hF0,  8'h3C);
        drive(3, 8'hFF,  8'h0F);
      end
      "random": begin
        t = new();
        repeat (n) begin
          if (t.randomize() == 0) $fatal(1, "randomize failed");
          drive(t.op, t.a, t.b);
        end
      end
      default: $fatal(1, "unknown TEST=%s", test);
    endcase
    @(negedge clk); in_valid = 0;
    repeat (3) @(negedge clk);
    $display("checked=%0d errors=%0d functional coverage=%0.1f%%", checked, errors, cg.get_coverage());
    if (errors == 0 && checked > 0) $display("TEST PASSED");
    else                            $display("TEST FAILED");
    $finish;
  end
endmodule
