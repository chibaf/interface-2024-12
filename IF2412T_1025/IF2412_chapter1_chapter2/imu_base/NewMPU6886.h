#ifndef _NEW_MPU6886_H_
#define _NEW_MPU6886_H_

/**
 * 6軸(角速度、加速度)センサ MPU6886 の改造ライブラリ
 * @version 0.01
 * @date    2023/1/13
 * @note    FreeRTOS対応版 割込み内で使用しないこと。
 */

#include <Wire.h>
#include <Arduino.h>

class NewMPU6886{
    public:
        enum Ascale {
            AFS_2G = 0,  // initial
            AFS_4G,
            AFS_8G,
            AFS_16G
        };

        enum Gscale {
            GFS_250DPS = 0,
            GFS_500DPS,  // initial
            GFS_1000DPS,
            GFS_2000DPS
        };

        enum Gfilter {
            // FCHOISE_B: 00
            GFIL_250 = 0,  // Rate 8kHz
            GFIL_176,      // Rate 1kHz initial
            GFIL_92,       // Rate 1kHz
            GFIL_41,       // Rate 1kHz
            GFIL_20,       // Rate 1kHz
            GFIL_10,       // Rate 1kHz
            GFIL_5,        // Rate 1kHz
            GFIL_3281,     // Rate 8kHz
            // FCHOISE_B: 10
            GNFIL_3281,    // Rate 32kHz
            // FCHOISE_B: X1
            GNFIL_8173     // Rate 32kHz
        };

        enum Afilter {
            // ACCEL_FCHOICE_B: 0
            AFIL_218 = 0,  // Rate 1kHz initial
            AFIL_99 = 2,   // Rate 1kHz
            AFIL_44,       // Rate 1kHz
            AFIL_21,       // Rate 1kHz
            AFIL_10,       // Rate 1kHz
            AFIL_5,        // Rate 1kHz
            AFIL_420,      // Rate 1kHz
            // ACCEL_FCHOICE_B: 1
            ANFIL_1046     // Rate 4kHz
        };

        NewMPU6886();
        ~NewMPU6886();

        bool init(uint8_t sda, uint8_t scl, uint8_t wire=1);

        void getAccelAdc(int16_t* ax, int16_t* ay, int16_t* az);
        void getGyroAdc(int16_t* gx, int16_t* gy, int16_t* gz);
        void getTempAdc(int16_t* t);
        void getAllAdc(int16_t* data);
        void getAllAdc(uint8_t* data);

        void getAccelData(float* ax, float* ay, float* az);
        void getGyroData(float* gx, float* gy, float* gz, bool is_radian=true);
        void getTempData(float* t);

        void setGyroFsr(Gscale scale);
        void setAccelFsr(Ascale scale);

        void setGyroFilter(Gfilter filter);
        void setAccelFilter(Afilter filter);

        void setSampleDivider(uint8_t div);
        void startFifo(bool accel_enable=true, bool gyro_enable=true);
        uint16_t getFifoSize(void);
        void getFifo(uint8_t *data, uint8_t size=1);
        void stopFifo(void);


        void setGyroXoffset(int16_t offset);
        void setGyroYoffset(int16_t offset);
        void setGyroZoffset(int16_t offset);

        void gyro_zero_cal(void);

    private:
        TwoWire *p_wire;
        Ascale now_ascale;
        Gscale now_gscale;
        Gfilter now_gfilter;
        Afilter now_afilter;
        uint8_t now_sample_divider;
        float aRes, gRes, gRadRes;
        SemaphoreHandle_t _semaphore;

        void I2C_Read_NBytes(uint8_t driver_Addr, uint8_t start_Addr, uint8_t number_Bytes, uint8_t *read_Buffer);
        void I2C_Write_NBytes(uint8_t driver_Addr, uint8_t start_Addr, uint8_t number_Bytes, uint8_t *write_Buffer);
        void getGres();
        void getAres();
};

#endif
