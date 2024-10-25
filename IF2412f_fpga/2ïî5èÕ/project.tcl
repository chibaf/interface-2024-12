# 使用する変数
set PRJ_NAME "hello_can"
set PART_NUM "GW5A-LV25MG121NES"
set DEV_VER "A"
set SRC_FILES {"./src/top.sv"
               "../../rtl/can_controller/can_controller.sv"
               "../../rtl/can_sender/can_sender.sv"
               "../../rtl/can_synchronizer/can_synchronizer.sv"
               "../../rtl/send_data_generator/send_data_generator.sv"}
set CST_FILES {"./src/physical.cst"}
set SDC_FILES {"./src/timing.sdc"}

# プロジェクトを作成
create_project -dir ../ \
               -name $PRJ_NAME \
               -pn $PART_NUM \
               -device_version $DEV_VER \
               -force

# System Verilog 2017 を使用することを指定
set_option -verilog_std sysv2017

# 各種ピンをGPIO として指定
set_option -use_i2c_as_gpio true
set_option -use_done_as_gpio true
set_option -use_ready_as_gpio true
set_option -use_cpu_as_gpio true

# ソースファイルを指定
foreach SRC_FILE $SRC_FILES {
  add_file -type verilog [file normalize $SRC_FILE]
}
# 物理制約ファイルを指定
foreach CST_FILE $CST_FILES {
  add_file -type cst [file normalize $CST_FILE]
}
# タイミング制約ファイルを指定
foreach SDC_FILE $SDC_FILES {
  add_file -type sdc [file normalize $SDC_FILE]
}

# 論理合成、配置配線、ビットストリーム生成を実行
run all
