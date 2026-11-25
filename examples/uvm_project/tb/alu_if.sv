// alu_if.sv - interface between the UVM testbench and the alu
`timescale 1ns/1ps
interface alu_if (input logic clk);
  logic       rst_n;
  logic       in_valid;
  logic [1:0] op;
  logic [7:0] a, b;
  logic       out_valid;
  logic [8:0] result;
endinterface
