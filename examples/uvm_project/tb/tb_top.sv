// tb_top.sv - top module: clock, reset, interface, DUT, starts the UVM test
// Waves: +WAVES writes waves.vcd (+WAVE_FILE=<name> to change the file name)
`timescale 1ns/1ps
module tb_top;
  import uvm_pkg::*;
  import alu_pkg::*;

  logic clk;
  initial clk = 0;
  always #5 clk = ~clk;   // 100 MHz

  alu_if vif (clk);

  alu dut (.clk(clk), .rst_n(vif.rst_n), .in_valid(vif.in_valid), .op(vif.op), .a(vif.a),
           .b(vif.b), .out_valid(vif.out_valid), .result(vif.result));

  initial begin
    vif.rst_n = 0;
    repeat (3) @(negedge clk);
    vif.rst_n = 1;
  end

  initial begin
    string wave_file;
    if ($test$plusargs("WAVES")) begin
      if (!$value$plusargs("WAVE_FILE=%s", wave_file)) wave_file = "waves.vcd";
      $dumpfile(wave_file);
      $dumpvars(0, tb_top);
    end
    uvm_config_db#(virtual alu_if)::set(null, "*", "vif", vif);
    run_test();
  end
endmodule
