import numpy as np
import matplotlib.pyplot as plt
from BleUart import BleUartClient
import asyncio
import threading
from queue import Queue
# 本誌提供のクオータニオンライブラリ(cq_quaternion.py)
from cq_quaternion import *
# Madgwick AHRSライブラリ https://github.com/Mayitzin/ahrs/tree/master
import ahrs


""" 回転する機体の姿勢角をリアルタイムに表示 (Madgwickフィルタ版)

プログラム実行すると、グラフ画面が現れ、リアルタイムに機体の姿勢を表示し続ける。
終了させるには、M5Stack ATOM-S3 のディスプレイ部(のボタン) を長押しする。

通常版と比べて、ドリフトが抑制されている。但しヨー角方向の回転の抑圧効果が
無いので、z軸周りの回転には弱い。3軸磁気センサも加えると、さらに改善可能。
"""

data_queue = Queue()
_DEVICE_NAME = "IMU_BASE"  # BLEデバイス名

async def imu_task():
    client = BleUartClient(_DEVICE_NAME)
    receive_queue = client.get_queue()
    await client.connect()
    if not client.is_connected():
        data_queue.put(None)
        return
    # IMUデータ連続送信 ON
    await client.write(b'b')
    point = -1
    q = Quaternion()
    # 角速度バイナリを rad/sec に変換するゲイン (+-250dps full scale)
    gyr_scale = 500/65536/180*math.pi
    while True:
        raw_data = await receive_queue.get()
        # 終了時のデータは、加速度センサ値6byte は、b'\x00'*6
        if raw_data[:6] == b'\x00'*6:
            data_queue.put(None)
            break   # exit while
        # (acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z)
        imu_data  = np.frombuffer(raw_data, dtype=np.int16).astype('float64')
        # 初回は加速度データから姿勢推定
        if point < 0:
            acc_data = imu_data[:3]
            # 初回は静置状態とし、加速度ベクトルから姿勢推定する
            # 基準座標は z軸が重力逆方向(上空)向きになる、人間視点の座標系
            rot_vec = outerProduct(acc_data, (0,0,1))  # 外積方向に
            rot_theta = crossAngle(acc_data, (0,0,1))  # ベクトル成す角
            q.setRotate(rot_vec, rot_theta)  # 回転させたクオータニオン
            q_arr = np.array(q.getValue())  # 時刻ゼロの回転クオータニオン
            # Madgwick 更新周波数:100Hz, beta:0.1
            # beta = 角速度を重視(小) ---> 加速度を重視(大)  0～1
            madgwick = ahrs.filters.Madgwick(None,None,None,frequency=100,beta=0.1)
            # 静止時の初期角速度をオフセット補正
            init_gyr = imu_data[3:]
            point += 1
        # 加速度、角速度からクオータニオン更新
        else:
            gyr_data = (imu_data[3:] - init_gyr)*gyr_scale
            acc_data = imu_data[:3]     # 加速度は単位不問
            q_arr = madgwick.updateIMU(q_arr, gyr_data, acc_data)
            point += 1
        # 0.25sec 毎に描画更新 メインスレッドへ、キュー送信
        if point % 25 == 0:
            now_q = Quaternion(*q_arr)
            conv_x = now_q.rotation((1,0,0))  # 機体座標系のx軸を、基準座標系に変換
            conv_y = now_q.rotation((0,1,0))  # 機体座標系のx軸を、基準座標系に変換
            conv_z = now_q.rotation((0,0,1))  # 機体座標系のz軸を、基準座標系に変換
            data_queue.put((conv_x, conv_y, conv_z))
            point = 0
    await client.disconnect()


def imu_io():
    asyncio.run(imu_task())


if __name__ == '__main__':
    print('Press the display button when finished.')
    # グラフ描画準備
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.grid()
    o = np.array([0,0,0])   # 原点
    # マイコンとの通信と姿勢計算は別スレッドで実施
    # メインスレッドは、別スレッドからのキューデータを受けて描画を担う
    sub_thread = threading.Thread(target=imu_io)
    sub_thread.start()
    while True:
        # サブスレッドからキューでデータ受信
        xyz_axis = data_queue.get()
        ax.clear()
        if xyz_axis is None:
            break   # exit while
        # 機体座標系 x 軸を、基準座標系に変換してベクトル表示
        ax.quiver(*o, *xyz_axis[0], color='r')  # x軸赤
        # 機体座標系 y 軸を、基準座標系に変換してベクトル表示
        ax.quiver(*o, *xyz_axis[1], color='b')  # y軸青
        # 機体座標系 z 軸を、基準座標系に変換してベクトル表示
        ax.quiver(*o, *xyz_axis[2], color='g')  # z軸緑
        ax.set_xlim(-1,1);ax.set_ylim(-1,1);ax.set_zlim(-1,1)
        plt.pause(.1)
    sub_thread.join()
