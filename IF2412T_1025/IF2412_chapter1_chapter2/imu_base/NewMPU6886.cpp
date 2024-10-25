#include "NewMPU6886.h"

/**
 * 6軸(角速度、加速度)センサ MPU6886 の改造ライブラリ
 * @version 0.01
 * @date    2023/1/13
 * @note    FreeRTOS対応版 割込み内で使用しないこと。
 */

#define MPU6886_ADDRESS           0x68 
#define MPU6886_WHOAMI            0x75
#define MPU6886_ACCEL_INTEL_CTRL  0x69
#define MPU6886_SMPLRT_DIV        0x19
#define MPU6886_INT_PIN_CFG       0x37
#define MPU6886_INT_ENABLE        0x38

#define MPU6886_ACCEL_XOUT_H      0x3B
#define MPU6886_ACCEL_XOUT_L      0x3C
#define MPU6886_ACCEL_YOUT_H      0x3D
#define MPU6886_ACCEL_YOUT_L      0x3E
#define MPU6886_ACCEL_ZOUT_H      0x3F
#define MPU6886_ACCEL_ZOUT_L      0x40

#define MPU6886_TEMP_OUT_H        0x41
#define MPU6886_TEMP_OUT_L        0x42

#define MPU6886_GYRO_XOUT_H       0x43
#define MPU6886_GYRO_XOUT_L       0x44
#define MPU6886_GYRO_YOUT_H       0x45
#define MPU6886_GYRO_YOUT_L       0x46
#define MPU6886_GYRO_ZOUT_H       0x47
#define MPU6886_GYRO_ZOUT_L       0x48

#define MPU6886_USER_CTRL         0x6A
#define MPU6886_PWR_MGMT_1        0x6B
#define MPU6886_PWR_MGMT_2        0x6C
#define MPU6886_CONFIG            0x1A
#define MPU6886_GYRO_CONFIG       0x1B
#define MPU6886_ACCEL_CONFIG      0x1C
#define MPU6886_ACCEL_CONFIG2     0x1D
#define MPU6886_FIFO_EN           0x23

#define MPU6886_XG_OFFS_USRH      0x13
#define MPU6886_XG_OFFS_USRL      0x14
#define MPU6886_YG_OFFS_USRH      0x15
#define MPU6886_YG_OFFS_USRL      0x16
#define MPU6886_ZG_OFFS_USRH      0x17
#define MPU6886_ZG_OFFS_USRL      0x18
#define MPU6886_ACCEL_XOUT_H      0x3B
#define MPU6886_ACCEL_XOUT_L      0x3C
#define MPU6886_ACCEL_YOUT_H      0x3D
#define MPU6886_ACCEL_YOUT_L      0x3E
#define MPU6886_ACCEL_ZOUT_H      0x3F
#define MPU6886_ACCEL_ZOUT_L      0x40
#define MPU6886_XA_OFFSET_H       0x77
#define MPU6886_XA_OFFSET_L       0x78
#define MPU6886_YA_OFFSET_H       0x7A
#define MPU6886_YA_OFFSET_L       0x7B
#define MPU6886_ZA_OFFSET_H       0x7D
#define MPU6886_ZA_OFFSET_L       0x7E
#define MPU6886_FIFO_COUNTH       0x72
#define MPU6886_FIFO_COUNTL       0x73
#define MPU6886_FIFO_R_W          0x74

#define MPU6886_CAL_AVG_TIMES     32

//#define G (9.8)
#define RtA     57.324841
#define AtR    	0.0174533	
#define Gyro_Gr	0.0010653

NewMPU6886::NewMPU6886(){
  _semaphore = xSemaphoreCreateMutex();
}

NewMPU6886::~NewMPU6886(){
  if(_semaphore){
        vSemaphoreDelete(_semaphore);
  }
}

void NewMPU6886::I2C_Read_NBytes(uint8_t driver_Addr, uint8_t start_Addr, uint8_t number_Bytes, uint8_t *read_Buffer){
  p_wire->beginTransmission(driver_Addr);
  p_wire->write(start_Addr);  
  p_wire->endTransmission(false);
  uint8_t i = 0;
  p_wire->requestFrom(driver_Addr,number_Bytes);
  
  //! Put read results in the Rx buffer
  while (p_wire->available()) {
    read_Buffer[i++] = p_wire->read();
  }
}

void NewMPU6886::I2C_Write_NBytes(uint8_t driver_Addr, uint8_t start_Addr, uint8_t number_Bytes, uint8_t *write_Buffer){
  p_wire->beginTransmission(driver_Addr);
  p_wire->write(start_Addr);
  p_wire->write(write_Buffer, number_Bytes);
  p_wire->endTransmission();
}

/**
 * @brief 初期化
 * @param[in] sda (uint8_t) I2CのSDA信号 GPIO番号
 * @param[in] scl (uint8_t) I2CのSCL信号 GPIO番号
 * @param[in] wire (uint8_t) 0:Wire , 1:Wire1
 * @return (bool) true: 成功, false: 失敗
 * @note
 *   初期条件は、加速度 +-2 g、角速度 +=500 degree/sec、
 */
bool NewMPU6886::init(uint8_t sda, uint8_t scl, uint8_t wire){
  unsigned char tempdata[1];
  unsigned char regdata;
  xSemaphoreTake(_semaphore, portMAX_DELAY);
  switch(wire){
    case 0:
      p_wire = &Wire;
      break;
    case 1:
      p_wire = &Wire1;
      break;
    default:
      p_wire = &Wire;
      break;
  }
  
  p_wire->begin((int)sda, (int)scl, (uint32_t)400000UL);  // 400kHz
  
  I2C_Read_NBytes(MPU6886_ADDRESS, MPU6886_WHOAMI, 1, tempdata);
  if(tempdata[0] != 0x19){
    xSemaphoreGive(_semaphore);
    return false;
  }
  delay(1);
  
  regdata = 0x00;
  I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_PWR_MGMT_1, 1, &regdata);
  delay(10);

  // reset all settings (auto clear after reset)
  regdata = (0x01<<7);
  I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_PWR_MGMT_1, 1, &regdata);
  delay(10);

  // Auto select clock
  regdata = (0x01<<0);
  I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_PWR_MGMT_1, 1, &regdata);
  delay(10);

  // Set accel range +-2g
  regdata = 0x00;
  I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_ACCEL_CONFIG, 1, &regdata);
  now_ascale = AFS_2G;
  delay(1);

  // Set gyro range +-500dps
  regdata = 0x08;
  I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_GYRO_CONFIG, 1, &regdata);
  now_gscale = GFS_500DPS;
  delay(1);

  // Configure gyro 3dB BW 176Hz Rate 1kHz
  // when the FIFO is full, additional writes will not be written to FIFO.
  regdata = 0x41;
  I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_CONFIG, 1, &regdata);
  now_gfilter = GFIL_176;
  delay(1);

  // Sample divider 0 (This register is only effective for inernal sampling rate 1kHz)
  // Data output rate or FIFO sampling rate = 1kHz / (this value + 1)
  regdata = 0x00;
  I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_SMPLRT_DIV, 1,&regdata);
  now_sample_divider = 0;
  delay(1);

  // Disable interrupt
  regdata = 0x00;
  I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_INT_ENABLE, 1, &regdata);
  delay(1);

  // Configure accel 3dB BW 218Hz Rate 1kHz
  regdata = 0x00;
  I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_ACCEL_CONFIG2, 1, &regdata);
  now_afilter = AFIL_218;
  delay(1);

  // Disable FIFO access from serial interface
  regdata = 0x00;
  I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_USER_CTRL, 1, &regdata);
  delay(1);

  // GYRO, ACCEL FIFO disable
  regdata = 0x00;
  I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_FIFO_EN, 1, &regdata);
  delay(1);

  // Configure INT pin
  regdata = 0x00;
  I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_INT_PIN_CFG, 1, &regdata);
  delay(1);

  // INT disable
  regdata = 0x00;
  I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_INT_ENABLE, 1, &regdata);
  xSemaphoreGive(_semaphore);

  delay(100);
  getGres();
  getAres();
  return true;
}

/**
 * @brief 加速度バイナリ値の取得
 * @param[inout] ax (int16_t *) x軸加速度センサバイナリ値
 * @param[inout] ay (int16_t *) y軸加速度センサバイナリ値
 * @param[inout] az (int16_t *) z軸加速度センサバイナリ値
 */
void NewMPU6886::getAccelAdc(int16_t* ax, int16_t* ay, int16_t* az){
   uint8_t buf[6];
   xSemaphoreTake(_semaphore, portMAX_DELAY);
   I2C_Read_NBytes(MPU6886_ADDRESS,MPU6886_ACCEL_XOUT_H,6,buf);
   xSemaphoreGive(_semaphore);
   *ax=((int16_t)buf[0]<<8)|buf[1];
   *ay=((int16_t)buf[2]<<8)|buf[3];
   *az=((int16_t)buf[4]<<8)|buf[5];
}

/**
 * @brief 角速度バイナリ値の取得
 * @param[inout] gx (int16_t *) x軸角速度センサバイナリ値
 * @param[inout] gy (int16_t *) y軸角速度センサバイナリ値
 * @param[inout] gz (int16_t *) z軸角速度センサバイナリ値
 */
void NewMPU6886::getGyroAdc(int16_t* gx, int16_t* gy, int16_t* gz){
  uint8_t buf[6];
  xSemaphoreTake(_semaphore, portMAX_DELAY);
  I2C_Read_NBytes(MPU6886_ADDRESS,MPU6886_GYRO_XOUT_H,6,buf);
  xSemaphoreGive(_semaphore);
  *gx=((uint16_t)buf[0]<<8)|buf[1];  
  *gy=((uint16_t)buf[2]<<8)|buf[3];  
  *gz=((uint16_t)buf[4]<<8)|buf[5];
}

/**
 * @brief 温度バイナリ値の取得
 * @param[inout] t (int16_t *) 温度バイナリ値
 */
void NewMPU6886::getTempAdc(int16_t *t){
  uint8_t buf[2];
  xSemaphoreTake(_semaphore, portMAX_DELAY);
  I2C_Read_NBytes(MPU6886_ADDRESS,MPU6886_TEMP_OUT_H,2,buf);
  xSemaphoreGive(_semaphore);
  *t=((uint16_t)buf[0]<<8)|buf[1];  
}

/**
 * @brief 角速度、加速度、温度値の取得
 * @param[inout] data (int16_t *) バイナリ値配列(7要素)
 * @note 7要素の連続データを格納。先頭から順に x,y,z軸角速度, 温度, x,y,z軸角速度
 */
void NewMPU6886::getAllAdc(int16_t* data){
   uint8_t buf[14];
   xSemaphoreTake(_semaphore, portMAX_DELAY);
   I2C_Read_NBytes(MPU6886_ADDRESS,MPU6886_ACCEL_XOUT_H,14,buf);
   xSemaphoreGive(_semaphore);
   *(data  )=((int16_t)buf[ 0]<<8)|buf[ 1];
   *(data+1)=((int16_t)buf[ 2]<<8)|buf[ 3];
   *(data+2)=((int16_t)buf[ 4]<<8)|buf[ 5];
   *(data+3)=((int16_t)buf[ 6]<<8)|buf[ 7];
   *(data+4)=((int16_t)buf[ 8]<<8)|buf[ 9];
   *(data+5)=((int16_t)buf[10]<<8)|buf[11];
   *(data+6)=((int16_t)buf[12]<<8)|buf[13];
}

/**
 * @brief 角速度、加速度、温度値の取得
 * @param[inout] data (uint8_t *) 2byteビッグエンディアン形式の2の補数符号付バイナリ値配列(14要素)
 * @note 7要素の連続データを格納。先頭から順に x,y,z軸角速度, 温度, x,y,z軸角速度
 *       但し、各要素は2byte のビッグエンディアンで2の補数表現の符号付16bit バイナリ値になる。
 */
void NewMPU6886::getAllAdc(uint8_t* data){
   xSemaphoreTake(_semaphore, portMAX_DELAY);
   I2C_Read_NBytes(MPU6886_ADDRESS,MPU6886_ACCEL_XOUT_H,14,data);
   xSemaphoreGive(_semaphore);
}

void NewMPU6886::getGres(){
   switch (now_gscale)
   {
  // Possible gyro scales (and their register bit settings) are:
     case GFS_250DPS:
           gRes = 250.0/32768.0;
           gRadRes = 250.0/32768.0/180.*3.14159265;
           break;
     case GFS_500DPS:
           gRes = 500.0/32768.0;
           gRadRes = 500.0/32768.0/180.*3.14159265;
           break;
     case GFS_1000DPS:
           gRes = 1000.0/32768.0;
           gRadRes = 1000.0/32768.0/180.*3.14159265;
           break;
     case GFS_2000DPS:
           gRes = 2000.0/32768.0;
           gRadRes = 2000.0/32768.0/180.*3.14159265;
           break;
     default:
           gRes = 0;
           gRadRes = 0;
   }
}

void NewMPU6886::getAres(){
   switch (now_ascale)
   {
   // Possible accelerometer scales (and their register bit settings) are:
   // 2 Gs (00), 4 Gs (01), 8 Gs (10), and 16 Gs  (11). 
   // Here's a bit of an algorith to calculate DPS/(ADC tick) based on that 2-bit value:
    case AFS_2G:
          aRes = 2.0/32768.0;
          break;
    case AFS_4G:
          aRes = 4.0/32768.0;
          break;
    case AFS_8G:
          aRes = 8.0/32768.0;
          break;
    case AFS_16G:
          aRes = 16.0/32768.0;
          break;
    default:
          aRes = 0;
          break;
  }
}

/**
 * @brief 角速度測定レンジ設定
 * @param[inout] scale (Gscale) レンジをマクロ値指定
 * @note GFS_250DPS, GFS_500DPS(initial), GFS_1000DPS, GFS_2000DPS
 */
void NewMPU6886::setGyroFsr(Gscale scale){
    unsigned char regdata;
    if(scale > GFS_2000DPS){
      return;
    }
    xSemaphoreTake(_semaphore, portMAX_DELAY);
    regdata = (scale<<3);
    if(now_gfilter == GNFIL_3281){
        regdata |= 0x02;
    }
    else if(now_gfilter == GNFIL_8173){
        regdata |= 0x01;
    }
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_GYRO_CONFIG, 1, &regdata);
    now_gscale = scale;
    getGres();
    xSemaphoreGive(_semaphore);
    delay(10);
}

/**
 * @brief 加速度測定レンジ設定
 * @param[inout] scale (Gscale) レンジをマクロ値指定
 * @note AFS_2G(initial), AFS_4G, AFS_8G, AFS_16G
 */
void NewMPU6886::setAccelFsr(Ascale scale){
    unsigned char regdata;
    if(scale > AFS_16G){
      return;	
    }
    xSemaphoreTake(_semaphore, portMAX_DELAY);
    regdata = (scale<<3);
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_ACCEL_CONFIG, 1, &regdata);
    now_ascale = scale;
    getAres();
    xSemaphoreGive(_semaphore);
    delay(10);
}

/**
 * @brief 加速度の取得
 * @param[inout] ax (float *) x軸加速度センサ値 [g]
 * @param[inout] ay (float *) y軸加速度センサ値 [g]
 * @param[inout] az (float *) z軸加速度センサ値 [g]
 */
void NewMPU6886::getAccelData(float* ax, float* ay, float* az){
  int16_t accX = 0;
  int16_t accY = 0;
  int16_t accZ = 0;
  getAccelAdc(&accX,&accY,&accZ);

  *ax = (float)accX * aRes;
  *ay = (float)accY * aRes;
  *az = (float)accZ * aRes;
}

/**
 * @brief 角速度の取得
 * @param[inout] gx (float *) x軸角速度センサ値 [g]
 * @param[inout] gy (float *) y軸角速度センサ値 [g]
 * @param[inout] gz (float *) z軸角速度センサ値 [g]
 * @param[in] is_radian (bool) 取得角速度の単位。true(デフォルト) なら [rad/s]。false なら [degree/s]
 */
void NewMPU6886::getGyroData(float* gx, float* gy, float* gz, bool is_radian){
  int16_t gyroX = 0;
  int16_t gyroY = 0;
  int16_t gyroZ = 0;
  getGyroAdc(&gyroX,&gyroY,&gyroZ);

  if(is_radian){
    *gx = (float)gyroX * gRadRes;
    *gy = (float)gyroY * gRadRes;
    *gz = (float)gyroZ * gRadRes;
  }
  else{
    *gx = (float)gyroX * gRes;
    *gy = (float)gyroY * gRes;
    *gz = (float)gyroZ * gRes;
  }
}

/**
 * @brief 温度の取得
 * @param[inout] t (float *) 温度センサ値 [degree]
 */
void NewMPU6886::getTempData(float *t){
  
  int16_t temp = 0;
  getTempAdc(&temp);
  
  *t = (float)temp / 326.8 + 25.0;
}

/**
 * @brief 角速度センサフィルタ設定
 * @param[in] filter (Gfilter) フィルタ設定をマクロ値指定
 * @note GFIL_250(Rate 8kHz), GFIL_176(Rate 1kHz ... initial),
         GFIL_92 (Rate 1kHz), GFIL_41 (Rate 1kHz),
         GFIL_20 (Rate 1kHz), GFIL_10 (Rate 1kHz),
         GFIL_5  (Rate 1kHz), GFIL_3281(Rate 8kHz),
         GNFIL_3281(Rate 32kHz), GNFIL_8173(Rate 32kHz)
 */
void NewMPU6886::setGyroFilter(Gfilter filter){
  uint8_t regdata;
  xSemaphoreTake(_semaphore, portMAX_DELAY);
  if(filter >= GFIL_250 || filter <= GFIL_3281){
    regdata = filter | 0x40;
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_CONFIG, 1, &regdata);
    regdata = (now_gscale << 3);
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_GYRO_CONFIG, 1, &regdata);
    now_gfilter = filter;
  }
  else if(filter == GNFIL_3281){
    regdata = (now_gscale << 3) | 0x02;
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_GYRO_CONFIG, 1, &regdata);
    now_gfilter = filter;
  }
  else if(filter == GNFIL_8173){
    regdata = (now_gscale << 3) | 0x01;
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_GYRO_CONFIG, 1, &regdata);
    now_gfilter = filter;
  }
  xSemaphoreGive(_semaphore);
  delay(1);
}

/**
 * @brief 加速度センサフィルタ設定
 * @param[in] filter (Afilter) フィルタ設定をマクロ値指定
 * @note AFIL_218(Rate 1kHz ... initial),
         AFIL_99 (Rate 1kHz), AFIL_44 (Rate 1kHz),
         AFIL_21 (Rate 1kHz), AFIL_10 (Rate 1kHz),
         AFIL_5  (Rate 1kHz), AFIL_420(Rate 1kHz),
         ANFIL_1046(Rate 4kHz)
 */
void NewMPU6886::setAccelFilter(Afilter filter){
  uint8_t regdata;
  xSemaphoreTake(_semaphore, portMAX_DELAY);
  if(filter >= AFIL_218 || filter <= AFIL_420){
    regdata = filter;
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_ACCEL_CONFIG2, 1, &regdata);
    now_afilter = filter;
  }
  else if(filter == ANFIL_1046){
    regdata = 0x08;
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_ACCEL_CONFIG2, 1, &regdata);
    now_afilter = filter;
  }
  xSemaphoreGive(_semaphore);
  delay(1);
}

/**
 * @brief サンプリング周波数(1kHzモードの時のみ有効) の分周設定
 * @param[in] div (uint8_t) 分周設定 1kHz/(div+1) がサンプリング周波数になる。
 */
void NewMPU6886::setSampleDivider(uint8_t divide){
    uint8_t regdata;
    // SAMPLE_RATE = INTERNAL_SAMPLE_RATE(1kHz) / (1 + div)
    regdata = divide;
    xSemaphoreTake(_semaphore, portMAX_DELAY);
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_SMPLRT_DIV, 1,&regdata);
    now_sample_divider = divide;
    xSemaphoreGive(_semaphore);
    delay(1);
}

/**
 * @brief FIFOをクリアしてスタート
 * @param[in] accel_enable (bool) 加速度データをFIFOログするかどうか デフォルト true
 * @param[in] gyro_enable (bool) 角速度データをFIFOログするかどうか デフォルト true
 * @note サンプリングレートは 1kHz Rate設定時は、1kHz/(div+1)  ※div は setSampleDivider() 設定値
 *   1サンプルでのデータ順 < accel_enable / gyro_enable >
 *   <true/false> : ACC_X_H, ACC_X_L, ... ACC_Z_H, ACC_Z_L, TEMP_H, TEMP_L (8byte)
 *   <false/true> : TEMP_H, TEMP_L, GYR_X_H, GYR_X_L, ... GYR_Z_H, GYR_Z_L (8byte)
 *   <true/true>  : ACC... TEMP... GYR... (14byte)
 */
void NewMPU6886::startFifo(bool accel_enable, bool gyro_enable){
    uint8_t regdata;
    xSemaphoreTake(_semaphore, portMAX_DELAY);
    // FIFO reset
    regdata = 0x04;
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_USER_CTRL, 1,&regdata);
    delay(1);
    // Enable FIFO operation
    regdata = 0x40;
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_USER_CTRL, 1,&regdata);
    // Enable accel or gyro FIFO
    regdata = 0;
    if(accel_enable){
      regdata |= 0x08;
    }
    if(gyro_enable){
      regdata |= 0x10;
    }
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_FIFO_EN, 1,&regdata);
    xSemaphoreGive(_semaphore);
}

/**
 * @brief FIFOに記録されたサイズ [byte]
 */
uint16_t NewMPU6886::getFifoSize(void){
    uint8_t count[2];
    xSemaphoreTake(_semaphore, portMAX_DELAY);
    I2C_Read_NBytes(MPU6886_ADDRESS, MPU6886_FIFO_COUNTH, 2, count);
    xSemaphoreGive(_semaphore);
    return (uint16_t)count[0] << 8 | count[1];
}

/**
 * @brief FIFOデータ取得
 * @param[out] data (uint8_t *) FIFO取得データを取得する配列
 * @param[in] size (uint8_t) 取得サイズ [byte] デフォルト 1
 * @note 無効データは 0xFF になる。size は 1サンプル蓄積バイト
 *       (Acc,Gyrどちらか片方なら8, 両方なら14) 以内とすること。
 */
void NewMPU6886::getFifo(uint8_t *data, uint8_t size){
    xSemaphoreTake(_semaphore, portMAX_DELAY);
    I2C_Read_NBytes(MPU6886_ADDRESS, MPU6886_FIFO_R_W, size, data);
    xSemaphoreGive(_semaphore);
}

/**
 * @brief FIFOログのストップ
 * @note FIFOバッファもクリアされる
 */
void NewMPU6886::stopFifo(void){
    uint8_t regdata;
    xSemaphoreTake(_semaphore, portMAX_DELAY);
    regdata = 0x00;
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_FIFO_EN, 1,&regdata);
    xSemaphoreGive(_semaphore);
}

/**
 * @brief x軸角速度の補正設定
 * @param[in] offset (int16_t) この値と、センサ生値が加算されて、getGyroData() からセンサ値取得出来るようになる。
 */
void NewMPU6886::setGyroXoffset(int16_t offset){
    uint8_t regarr[2];
    
    switch(now_gscale){
      case GFS_250DPS:
        offset /= 4;
        break;
      case GFS_500DPS:
        offset /= 2;
        break;
      case GFS_2000DPS:
        offset *= 2;
        break;
      default:
        break;
    }

    regarr[0] = (uint8_t) ((offset >> 8) & 0x00ff);
    regarr[1] = (uint8_t) (offset & 0x00ff);
    xSemaphoreTake(_semaphore, portMAX_DELAY);
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_XG_OFFS_USRH, 2,regarr);
    xSemaphoreGive(_semaphore);
    delay(1);
}

/**
 * @brief y軸角速度の補正設定
 * @param[in] offset (int16_t) この値と、センサ生値が加算されて、getGyroData() からセンサ値取得出来るようになる。
 */
void NewMPU6886::setGyroYoffset(int16_t offset){
    uint8_t regarr[2];
    
    switch(now_gscale){
      case GFS_250DPS:
        offset /= 4;
        break;
      case GFS_500DPS:
        offset /= 2;
        break;
      case GFS_2000DPS:
        offset *= 2;
        break;
      default:
        break;
    }
    regarr[0] = (uint8_t) ((offset >> 8) & 0x00ff);
    regarr[1] = (uint8_t) (offset & 0x00ff);
    xSemaphoreTake(_semaphore, portMAX_DELAY);
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_YG_OFFS_USRH, 2,regarr);
    xSemaphoreGive(_semaphore);
    delay(1);
}

/**
 * @brief z軸角速度の補正設定
 * @param[in] offset (int16_t) この値と、センサ生値が加算されて、getGyroData() からセンサ値取得出来るようになる。
 */
void NewMPU6886::setGyroZoffset(int16_t offset){
    uint8_t regarr[2];
    
    switch(now_gscale){
      case GFS_250DPS:
        offset /= 4;
        break;
      case GFS_500DPS:
        offset /= 2;
        break;
      case GFS_2000DPS:
        offset *= 2;
        break;
      default:
        break;
    }
    regarr[0] = (uint8_t) ((offset >> 8) & 0x00ff);
    regarr[1] = (uint8_t) (offset & 0x00ff);
    xSemaphoreTake(_semaphore, portMAX_DELAY);
    I2C_Write_NBytes(MPU6886_ADDRESS, MPU6886_ZG_OFFS_USRH, 2,regarr);
    xSemaphoreGive(_semaphore);
    delay(1);
}

/**
 * @brief 角速度センサのオフセット補正
 * @note
 *   静止状態にして、本関数を呼び出す。角速度を測定し、正負反転値を
 *   オフセットに設定する。
 */
void NewMPU6886::gyro_zero_cal(void){
  int16_t gyrX, gyrY, gyrZ;
  int32_t avgX, avgY, avgZ;

  avgX=0; avgY=0; avgZ=0;
  for(uint16_t i=0; i < MPU6886_CAL_AVG_TIMES; ++i){
      getGyroAdc(&gyrX, &gyrY, &gyrZ);
      delay(10);
      avgX += gyrX; avgY += gyrY; avgZ += gyrZ;
  }
  setGyroXoffset(-avgX/MPU6886_CAL_AVG_TIMES);
  setGyroYoffset(-avgY/MPU6886_CAL_AVG_TIMES);
  setGyroZoffset(-avgZ/MPU6886_CAL_AVG_TIMES);
}
