`default_nettype none

module top (
  input  wire clk,  // クロック入力
  output wire err,  // エラー出力
  // CAN トランシーバ(TJA1441AT) とのインターフェース
  output wire txd,  // データ送信線
  input  wire rxd,  // データ受信線
  output wire s     // モードセレクト: 0 -> Normal mode / 1 -> Silent mode
);

  localparam CLK_FREQ_HZ    = 50_000_000;   // 入力クロック周波数
  localparam CAN_BITRATE_HZ = 500_000;      // CAN のビットレート
  localparam SLEEP_CYCLE    = CLK_FREQ_HZ;  // データ送信後、スリープするcycle 数

  // Normal mode に固定
  assign s = 1'b0;

  // モジュール間の接続に使用する変数
  wire status_warning;
  wire status_bus_off;
  wire [63:0] stm_send_data_tdata;
  wire [10:0] stm_send_data_tid;
  wire [7:0]  stm_send_data_tkeep;
  wire        stm_send_data_tvalid;
  wire        stm_send_data_tready;
  wire [2:0]  stm_result_tdata;
  wire        stm_result_tvalid;
  wire        stm_result_tready;

  ///////// 送信データを生成するモジュール /////////
  send_data_generator #(
    .SLEEP_CYCLE(SLEEP_CYCLE)
  ) send_data_generator_i (
    .stm_send_data_out_tdata (stm_send_data_tdata),
    .stm_send_data_out_tid   (stm_send_data_tid),
    .stm_send_data_out_tkeep (stm_send_data_tkeep),
    .stm_send_data_out_tvalid(stm_send_data_tvalid),
    .stm_send_data_out_tready(stm_send_data_tready),
    .stm_result_in_tdata     (stm_result_tdata),
    .stm_result_in_tvalid    (stm_result_tvalid),
    .stm_result_in_tready    (stm_result_tready),
    .*
  );

  ///////// CAN コントローラ /////////
  can_controller #(
    .CLK_FREQ_HZ(CLK_FREQ_HZ),
    .CAN_BITRATE_HZ(CAN_BITRATE_HZ)
  ) can_controller_i (
    .stm_send_data_in_tdata (stm_send_data_tdata),
    .stm_send_data_in_tid   (stm_send_data_tid),
    .stm_send_data_in_tkeep (stm_send_data_tkeep),
    .stm_send_data_in_tvalid(stm_send_data_tvalid),
    .stm_send_data_in_tready(stm_send_data_tready),
    .stm_result_out_tdata   (stm_result_tdata),
    .stm_result_out_tvalid  (stm_result_tvalid),
    .stm_result_out_tready  (stm_result_tready),
    .*
  );

  ///////// エラーの有無を外部に出力するロジック /////////
  logic err_reg = 'd0;
  assign err = err_reg;
  always_ff @ (posedge clk) begin
    if (stm_result_tvalid & stm_result_tready) begin
      err_reg <= |stm_result_tdata;
    end
  end

endmodule

`default_nettype wire
