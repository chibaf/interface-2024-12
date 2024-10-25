#include <Arduino.h>
#include "NuSerial.hpp"
#include "NimBLEDevice.h"
#include "NewMPU6886.h"

/* Interface 2024年12月号

<ハードウェア構成>
  - M5Stack Atom S3   https://docs.m5stack.com/en/core/AtomS3
  - TailBat           https://docs.m5stack.com/en/atom/tailbat

<プログラム環境>
Arduino IDE ver.2.3.2
BOARDS MANAGER : M5Stack Arduino 2.0.7 , M5Stack-ATOMS3
LIBRARY MANAGER:
    NimBLE-Arduino 1.4.2
    NuS-NimBLE-Sereal 2.0.4
    IMU制御用ライブラリは、直下に自作 NewMPU6886.h / NewMPU6886.cpp をコピー

<通信>
  BLE Nordic UARTサービスのサーバーとして機能する。
  PCからのコマンド(英字一文字終端文字なし)を受けて、コマンド実行する。

<動作状態>
  STATE_IDLE     ... 待機状態
  STATE_ONESHOT  ... 1回だけの IMUデータを即時取得する、取得後自動的に待機状態に移行
  STATE_SAMPLING ... 10ms毎に連続して IMUデータを取得し続ける

<状態遷移>
  STATE_IDLE -> STATE_ONESHOT    : PCから "s" 受信
  STATE_ONESHOT -> STATE_IDLE    : 1回だけの IMUデータを即時取得したら、自動で待機状態に戻る

  STATE_IDLE -> STATE_SAMPLING   : PCから "b" 受信、または、M5Stack Atom S3 のディスプレイを 200ms以上押し込んで離す
  STATE_SAMPLING -> STATE_IDLE   : PCから "e" 受信、または、M5Stack Atom S3 のディスプレイを 200ms以上押し込んで離す

<IMUデータ受信フォーマット>
  M5Stack Atom S3 から PC に送られるデータは、notify データとして送られる。
  1回の notify データは、1回の IMUデータサンプリングに対応する 12byte とする。
  12byte データは、バイナリ / signed 16bit / little endian 形式とする。12byte は順に以下の通り、
      acc_x(L) acc_x(H) acc_y(L) acc_y(H) acc_z(L) acc_z(H) gyr_x(L) gyr_x(H) gyr_y(L) gyr_y(H) gyr_z(L) gyr_z(H)
  STATE_SAMPLING で得られる IMUデータは、終端データ(12byte 全て0) によってデータ完了を判断する。
*/


NewMPU6886 imu;
static constexpr uint8_t I2C_SDA_PIN = 38;      // M5Stack ATOM S3 sda pin
static constexpr uint8_t I2C_SCL_PIN = 39;      // M5Stack ATOM S3 scl pin
static constexpr uint8_t  BUTTON_PIN = 41;      // Front button

static TickType_t xPERIOD = pdMS_TO_TICKS(10);  // Refresh rate 10msec

static constexpr uint8_t STATE_IDLE     = 0;
static constexpr uint8_t STATE_SAMPLING = 1;
static constexpr uint8_t STATE_ONESHOT  = 2;
static constexpr uint8_t STATE_GET_LOG  = 3;
static constexpr uint8_t STATE_LOGGING  = 8;
static uint8_t now_state = STATE_IDLE;

const  int16_t end_data[6] = {0,0,0,0,0,0};  // Terminate data for end of STATE_SAMPLING

static uint8_t checkButton(uint8_t is_push, uint8_t state);

void setup(){
    imu.init(I2C_SDA_PIN, I2C_SCL_PIN, 0);
    imu.setAccelFsr(NewMPU6886::AFS_2G);    // +-2g range
    imu.setGyroFsr(NewMPU6886::GFS_250DPS); // +-250degree/s range
    imu.setAccelFilter(NewMPU6886::AFIL_44);   // Filter cutoff 44Hz
    imu.setGyroFilter(NewMPU6886::GFIL_41);    // Filter cutoff 41Hz
    imu.stopFifo();
    pinMode(BUTTON_PIN, INPUT);
    // BLE Nordic UART Service UUID : 6E400001-B5A3-F393-E0A9-E50E24DCCA9E
    //   |-- RX characteristic UUID (write) : 6E400002-B5A3-F393-E0A9-E50E24DCCA9E
    //   |-- TX characteristic UUID (notify): 6E400003-B5A3-F393-E0A9-E50E24DCCA9E
    NimBLEDevice::init("IMU_BASE");  // Device name
    NuSerial.begin(115200);
}

void loop(){
    TickType_t xLastWakeTime;
    static uint32_t write_point = 0;
    int16_t log_data[6];

    xLastWakeTime = xTaskGetTickCount();

    // Check front button
    now_state = checkButton(!digitalRead(BUTTON_PIN), now_state);
    
    // Check command from BLE
    if(NuSerial.isConnected() && NuSerial.available()){
        int command = NuSerial.read();
        if(now_state != STATE_LOGGING){
            switch(command){
                case 'b':
                    now_state = STATE_SAMPLING;
                    break;
                case 'e':
                    if(now_state == STATE_SAMPLING){
                        NuSerial.write((uint8_t *)end_data, 6*2);
                    }
                    now_state = STATE_IDLE;
                    break;
                case 's':
                    if(now_state == STATE_IDLE){
                        now_state = STATE_ONESHOT;
                    }
                    break;
                default:
                    break;
            }
        }
    }

    // Action for state
    if(now_state == STATE_SAMPLING || now_state == STATE_ONESHOT){
        imu.getAccelAdc(log_data, log_data+1, log_data+2);
        imu.getGyroAdc(log_data+3, log_data+4, log_data+5);
        // IMU data ==> signed 16bit little endian 12byte binary
        //   |-- acc_x(L) acc_x(H) acc_y(L) acc_y(H) acc_z(L) acc_z(H)
        //       gyr_x(L) gyr_x(H) gyr_y(L) gyr_y(H) gyr_z(L) gyr_z(H)
        NuSerial.write((uint8_t *)log_data, 6*2);            
        if(now_state == STATE_ONESHOT){
            now_state = STATE_IDLE;
        }
    }

    vTaskDelayUntil(&xLastWakeTime, xPERIOD);
}

uint8_t checkButton(uint8_t is_push, uint8_t state){
    // Detects the continuous button press time to prevent chattering.
    constexpr uint16_t ACTIVATE_TIMES = 20;
    static uint16_t push_times = 0;

    // Push button
    if(is_push){
        // Judgment based on the number of consecutive times
        // Ignore overflow
        ++push_times;
    }
    // Release button
    else{
        if(push_times > ACTIVATE_TIMES){
            push_times = 0;
            if(state == STATE_IDLE){
                // Waiting time to avoid button impact
                delay(1500);
                return STATE_SAMPLING;
            }
            else if(state == STATE_SAMPLING){
                NuSerial.write((uint8_t *)end_data, 6*2);
                return STATE_IDLE;
            }
        }
        else{
            push_times = 0;
        }
    }
    return state;
}
