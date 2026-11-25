// alu_sva.sv - assertions for alu, attached with bind (no change to the RTL needed)
`timescale 1ns/1ps
module alu_sva (
  input logic       clk,
  input logic       rst_n,
  input logic       in_valid,
  input logic [1:0] op,
  input logic [7:0] a,
  input logic [7:0] b,
  input logic       out_valid,
  input logic [8:0] result
);
  // out_valid follows in_valid one clock later
  a_valid_latency: assert property (@(posedge clk) disable iff (!rst_n)
    in_valid |=> out_valid) else $error("out_valid did not follow in_valid");

  // no output without an input in the previous cycle
  a_no_spurious: assert property (@(posedge clk) disable iff (!rst_n)
    !in_valid |=> !out_valid) else $error("out_valid without in_valid");

  // ADD result is correct one clock later
  a_add_ok: assert property (@(posedge clk) disable iff (!rst_n)
    (in_valid && op == 2'd0) |=> result == $past({1'b0, a}) + $past({1'b0, b}))
    else $error("ADD result wrong");

  // after reset, out_valid is low
  a_reset: assert property (@(posedge clk) !rst_n |=> !out_valid)
    else $error("out_valid high after reset");

  // cover: back-to-back valid inputs, and an ADD with carry out
  c_back_to_back: cover property (@(posedge clk) disable iff (!rst_n) in_valid ##1 in_valid);
  c_add_carry:    cover property (@(posedge clk) disable iff (!rst_n)
    in_valid && op == 2'd0 ##1 result[8]);
endmodule

// attach the checker to every instance of alu
bind alu alu_sva u_alu_sva (.*);
