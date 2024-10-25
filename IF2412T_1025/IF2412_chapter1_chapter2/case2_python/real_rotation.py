import numpy as np
import matplotlib.pyplot as plt
from BleUart import BleUartClient
import asyncio
import threading
from queue import Queue
# 本誌提供のクオータニオンライブラリ(cq_quaternion.py)
from cq_quaternion import *

""" 回転する機体の姿勢角をリアルタイムに表示

プログラム実行すると、グラフ画面が現れ、リアルタイムに機体の姿勢を表示し続ける。
終了させるには、M5Stack ATOM-S3 のディスプレイ部(のボタン) を長押しする。
"""

data_queue = Queue()
_DEVICE_NAME = "IMU_BASE"  # BLEデバイス名
_INTERVAL = 0.01           # データサンプリング間隔 10msec

async def imu_task():
    """6軸慣性センサのデータサンプリングタスク"""
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
    gyr_scale = 2*250/65536/180*math.pi
    while True:
        # 1回の受信データは、12バイト。6軸バイナリデータ x 2バイト/データ
        # 6軸データは、xyz加速度、xyz角速度の順
        raw_data = await receive_queue.get()
        # M5Stack ATOM-S3 のディスプレイボタンを押すとIMUデータ送信終了
        # 終了時のデータは、b'\x00'*12が来るので、連続6バイトゼロで判断する。
        if raw_data[:6] == b'\x00'*6:
            # キューに None 送ると、プログラム終了の通知
            data_queue.put(None)
            break   # exit while
        # バイナリデータ列は、符号付16bitリトルエンディアン形式なので、int16型に復元
        imu_data  = np.frombuffer(raw_data, dtype=np.int16).astype('float64')
        # 初回は静置状態とし、加速度ベクトルから姿勢推定する
        # 基準座標は z軸が重力逆方向(上空)向きになる、人間視点の座標系
        if point < 0:
            acc_data = imu_data[:3]
            # 基準座標z軸と重力方向の外積方向を中心軸として
            rot_vec = outerProduct(acc_data, (0,0,1))
            # 基準座標z軸と重力方向の成す角が
            rot_theta = crossAngle(acc_data, (0,0,1))
            # 初回の基準座標からの機体座標への回転クオータニオンになる
            q.setRotate(rot_vec, rot_theta)
            # 静止時の初期角速度をオフセット値とする
            init_gyr = imu_data[3:]
            point += 1
        # 角速度からクオータニオン更新
        else:
            # 角速度バイナリ出力からオフセット減算し、rad/sec に変換するゲイン積算
            gyr_data = (imu_data[3:] - init_gyr)*gyr_scale
            # 角速度[rad/sec] から、式(15) で回転クオータニオン更新
            q.integralAngleVelocity(gyr_data, _INTERVAL)
            point += 1
        # 0.25sec 毎に描画更新 メインスレッドへ、キュー送信
        if point % 25 == 0:
            conv_x = q.rotation((1,0,0))  # 機体座標系のx軸を、基準座標系に変換
            conv_y = q.rotation((0,1,0))  # 機体座標系のy軸を、基準座標系に変換
            conv_z = q.rotation((0,0,1))  # 機体座標系のz軸を、基準座標系に変換
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
    # 別スレッドの終了を待つ
    sub_thread.join()
