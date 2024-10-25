import numpy as np
import matplotlib.pyplot as plt
# 本誌オリジナルのクオータニオン演算ライブラリ
from cq_quaternion import *

""" 取得した6軸IMUデータからオイラー角を表示

sampling.py により10秒間取得した6軸IMUデータから、
センサの姿勢を示すオイラー角を計算して表示
"""

# numpy形式データファイル
_SAVE_FILE = "sampling.npy"
# データサンプリング間隔 [sec]
_INTERVAL = 0.01

# sampling.py で収集した6軸慣性センサバイナリデータ
# imu.shape -> (サンプル点, 6) の次元
# 6 の要素は、x,y,z加速度、x,y,z角速度の順
imu = np.load(_SAVE_FILE).astype('float64')
# 基準座標系は時刻ゼロ時の機体座標とする。
# 機体座標 = 基準座標 = 回転ゼロ の回転クオータニオンは 1
q = Quaternion(1,0,0,0)
# 各時刻のオイラー角格納データ
euler = []
# 時刻ゼロの角速度データは、静置とみなし、オフセット補正
# ゲインは理論値(±250dpsフルレンジ)を、[rad/sec] に変換
gyr = (2*250/65536*np.pi/180)*(imu[:, 3:] - imu[0, 3:])
for i in range(gyr.shape[0]):
    # 角速度[rad/sec] から、式(15) で回転クオータニオン更新
    q.integralAngleVelocity(gyr[i, :], _INTERVAL)
    # クオータニオンからオイラー角 [rad]へ変換 式(16-18)
    euler.append(q.getEuler())
# オイラー角の単位をラジアンから度に変換
euler_arr = (180/np.pi) * np.array(euler)
plt.plot(euler_arr[:,0], label='roll')
plt.plot(euler_arr[:,1], label='pitch')
plt.plot(euler_arr[:,2], label='yaw')
plt.legend()
plt.show()
