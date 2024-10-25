import numpy as np
import matplotlib.pyplot as plt

""" ファイル保存された 6軸IMUデータから、加速度センサ校正 

sample_one.py で、IMUセンサを回転させながら、静置状態で IMUデータを取得し、ファイル保存。
そのファイルのデータから、加速度センサの校正を行う。

校正後は、加速度ベクトルの大きさが 9.80665 [m^2/sec] になる。

[:, 0] => x軸加速度バイナリ (-32768～+32767 が -2g～+2g に対応)
[:, 1] => y軸加速度バイナリ (-32768～+32767 が -2g～+2g に対応)
[:, 2] => z軸加速度バイナリ (-32768～+32767 が -2g～+2g に対応)
[:, 3] => x軸角速度バイナリ (-32768～+32767 が -250dps～+250dps に対応)
[:, 4] => y軸角速度バイナリ (-32768～+32767 が -250dps～+250dps に対応)
[:, 5] => z軸角速度バイナリ (-32768～+32767 が -250dps～+250dps に対応)
"""

_SAVE_FILE = "sample_one.npy"
ACC_G = 9.80665

def plot_3d(x):
    """ 3次元座標を点プロット

    Parameters
    -----
    x: np.array
        2次元アレイで、shape = (サンプル点数, 3) の3次元座標群
    """
    fig = plt.figure(figsize = (8, 8))
    ax= fig.add_subplot(111, projection='3d')
    # 点プロット
    ax.scatter(x[:,0],x[:,1],x[:,2])
    plt.show()

# sample_one.py で収集した静置時 IMUデータ
imu = np.load(_SAVE_FILE).astype('float64')
# 確認のため、加速度3軸データを3次元プロット
plot_3d(imu[:,:3])
# imu.shape => (サンプル点数,6)
# 66点のサンプル点, 3軸磁気センサバイナリ値
# 6軸IMUデータは、x, y, z軸加速度, x, y, z角速度のの順番に格納
# ex) imu[19, 1] => 20サンプル目の y軸加速度(-32768～+32767 が -2g～+2g に対応)

# まずは説明変数の読み替え
x0 = imu[:,1]*imu[:,1]  # acc_y^2
x1 = imu[:,2]*imu[:,2]  # acc_z^2
x2 = imu[:,0]  # acc_x
x3 = imu[:,1]  # acc_y
x4 = imu[:,2]  # acc_z
x5 = np.ones(imu.shape[0])  # 1
# 説明変数行列 X
X = np.stack([x0, x1, x2, x3, x4, x5], axis=1)
# 目的変数ベクトル y
y = -1*imu[:,0]*imu[:,0]  # -mx^2
# 正規方程式の解 偏回帰ベクトル k
ans = np.linalg.lstsq(X, y, None)
k = ans[0]
# 重力加速度を 9.80665 [m2/sec] とする
r = ACC_G
# 各軸のオフセットb、ゲインa
rmd = -k[5]+k[2]**2/4+k[3]**2/(4*k[0])+k[4]**2/(4*k[1])
a_x = r*np.sqrt(1/rmd)    # x軸補正ゲイン
a_y = r*np.sqrt(k[0]/rmd) # y軸補正ゲイン
a_z = r*np.sqrt(k[1]/rmd) # z軸補正ゲイン
b_x = -k[2]/2             # x軸オフセット
b_y = -k[3]/(2*k[0])      # y軸オフセット
b_z = -k[4]/(2*k[1])      # z軸オフセット
print("x軸ゲイン : {}".format(a_x))
print("y軸ゲイン : {}".format(a_y))
print("z軸ゲイン : {}".format(a_z))
print("x軸オフセット : {}".format(b_x))
print("y軸オフセット : {}".format(b_y))
print("z軸オフセット : {}".format(b_z))

# 校正後のプロット
offset = np.array([b_x, b_y, b_z])
gain = np.array([a_x, a_y, a_z])
plot_3d(gain * (imu[:,:3] - offset))
