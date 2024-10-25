# Interface 2024年12月号
# 線形代数
# DBFレーダーのアナログ波形の生成
#　(c) 米本成人
#   July, 2023

#Google colabを利用する時は下の#を外して!pipでインストールすること
#!pip install japanize-matplotlib

import japanize_matplotlib#日本語用malolib
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D      ### 3Dなら必要

#符号化された送信機に対する受信信号の演算
#アダマール行列の定義
#　アダマール行列の定義
#　引数のorderは２の階乗の数字である事。　
def hadamard_matrix(order):
    if order == 1:
        return np.array([[1]])#2**0＝1の時は１
    else:
        H_n = hadamard_matrix(order // 2)#orderを２で割った数字で自分を呼ぶ
        top = np.hstack((H_n, H_n))#もらったH_nを２つ水平方向に並べる
        bottom = np.hstack((H_n, -H_n))#もらったH_nとH_nを水平方向に並べる
        return np.vstack((top, bottom))#topとbottomを垂直方向に並べる

    
# 例として、16次のアダマール行列を生成する
order = 16#行列の幅
H = hadamard_matrix(order)#関数呼び出し

# 行列のサイズを取得して表示する
print("\nSize of the matrix H:", H.shape)

#レーダーのパラメータ設定
MaxRange = 100#最大距離
ViewAngle = 30#視野角
N=MaxRange*2+2#サンプル数1メモリ1mとして、0からMaxRangeまで
dt = 1/(N-1)#サンプリング周期
M = 16 #アンテナ数
mu, sigma = 0.0, 1 #ノイズの平均値、標準偏差


Harray_3d = np.repeat(H[:, :, np.newaxis], N, axis=2)
# 行列のサイズを取得して表示する
print("\nSize of the matrix Harray3D:", Harray_3d.shape)


H2D = Harray_3d.reshape(Harray_3d.shape[0], -1)
print("\nSize of the matrix H2D:", H2D.shape)

#データ描画
antenna = np.linspace(1,M,M)#アンテナ番号
timemax = H2D.shape[1]
time = np.linspace(1,timemax,timemax)
x_mesh, y_mesh = np.meshgrid(time, antenna)#アンテナ番号と符号列のビットに合わせたメッシュデータを作る

antenna = np.linspace(1,M,M)#アンテナ番号
angle = np.pi*np.linspace(-ViewAngle/2, ViewAngle/2,M)/180#アンテナの画角設定（radian）
distance = np.linspace(0,N,N)#距離(m)
t = np.linspace(0, 1, N) # 時間 [s]

# 3D描画用のmeshgrid を作成
range_mesh, antenna_mesh = np.meshgrid(distance, antenna)#アンテナ番号と距離に合わせたメッシュデータを作る
range_mesh, angle_mesh = np.meshgrid(distance, angle)#角度と距離に合わせたメッシュデータを作る。
radar_x_mesh = range_mesh * np.sin(angle_mesh)#レーダーからみて横方向の座標をX軸とする
radar_y_mesh = range_mesh * np.cos(angle_mesh)#レーダーから見て距離方向の座標をY軸とする
x1, x2 = np.array_split(radar_x_mesh, 2, 1)#メッシュデータを分割して必要なところだけ使う
y1, y2 = np.array_split(radar_y_mesh, 2, 1)#メッシュデータを分割して必要なところだけ使う

#データ作成
#とりあえず空の行列を作る
noisedata = 0*range_mesh
signaldata= 0*range_mesh
#２つの物体からの反射波の周波数、振幅、および到来角を設定。
f1, f2 = 50, 90    # 周波数 [kHz]
a1, a2 = 10,5        # 振幅
p1, p2 = -12, 5    # 位相（度）
for m in range(M):
#    noisedata[m]=np.random.normal(mu, sigma, N)#ノイズ
    signaldata[m]=a1*np.cos(2*np.pi*(f1*t+p1*m/ViewAngle)) + a2*np.sin(2*np.pi*(f2*t+p2*m/ViewAngle)) # 信号

noisedata= np.random.randn(*signaldata.shape)
timedomaindata = signaldata

fig6 = plt.figure(6)
ax = fig6.add_subplot(projection='3d')
for i in range(x_mesh.shape[0]):
    ax.plot(range_mesh[M-i-1], antenna_mesh[M-i-1], timedomaindata[M-i-1])
plt.yticks([1,6,11,16])#y方向の目盛
ax.set_title("各送信機に対するビート信号") #グラフタイトルを設定
ax.set_xlabel("時間列", color="black")#軸ラベル
ax.set_ylabel("アンテナ番号",color="black")
plt.savefig("./Fig6.png") #図の保存

repeat_times=M;#パルス繰り返し数

array_3d = np.repeat(timedomaindata[:,  np.newaxis,:], repeat_times, axis=1)
print("\nSize of the matrix array3D:", array_3d.shape)

array_2D = array_3d.reshape(array_3d.shape[0], -1)
print("\nSize of the matrix array2D:", array_2D.shape)

Coded_Signal=H2D*array_2D#要素の掛け算
print("\nSize of the coded signal matrix :", Coded_Signal.shape)

# 1軸（2番目の軸）に沿って要素を足し合わせて2次元配列を作成
rx = np.sum(Coded_Signal, axis=0)
noisedata= np.random.randn(*rx.shape)
received_signal=rx+noisedata
print("\nSize of the received signal:", received_signal.shape)

timeno =16*202
time = np.linspace(0, 16, timeno) # 時間 [s]
fig7= plt.figure(7)
ax = fig7.add_subplot()
ax.plot(x_mesh[0], received_signal)
ax.set_title("受信波と種FMCW信号のミキシングから得られるビート信号") #グラフタイトルを設定
ax.set_xlabel("時間列", color="black")#軸ラベル
ax.set_ylabel("振幅",color="black")
plt.savefig("./Fig7.png") #図の保存

#
#複号処理
#

#符号化された送信機に対する受信信号の演算
Rx_2D = np.repeat(received_signal[np.newaxis,:], repeat_times, axis=0)
print("\nCopy the received signal:", received_signal.shape)

Correlated_data = H2D*Rx_2D#要素の掛け算
print("\nCalculation of correlation:", Correlated_data.shape)

Correlated_3Ddata = Correlated_data.reshape(array_3d.shape)
print("\nCalculation of correlation:", Correlated_3Ddata.shape)

Reconstructed_signal = np.sum(Correlated_3Ddata, axis=1)
print("\nReconstructed 2D raw data:", Reconstructed_signal.shape)

fig8 = plt.figure(8)
ax = fig8.add_subplot(projection='3d')
for i in range(x_mesh.shape[0]):
    ax.plot(range_mesh[M-i-1], antenna_mesh[M-i-1], Reconstructed_signal[M-i-1])
plt.yticks([1,6,11,16])#y方向の目盛
ax.set_title("復元された受信信号") #グラフタイトルを設定
ax.set_xlabel("時間列", color="black")
ax.set_ylabel("アンテナ番号",color="black")#軸ラベル
ax.set_zlabel("信号",color="black")
plt.savefig("./Fig8.png") #図の保存

#
#   各種信号処理
#
#   2DFFT
fftdata = np.fft.fft2(Reconstructed_signal) #2次元FFT
absdata = abs(fftdata)#振幅計算
magdata = 20*np.log10(absdata)#dB換算
posdata, negadata = np.array_split(magdata, 2, 1)#ベースバンドを正の周波数と負の周波数に分割
leftdata, rightdata = np.array_split(posdata, 2)#左右に分割
mapdata = np.vstack([rightdata, leftdata])#タイリングでFFTの折り返しを無くす

#フィルタ作成
theta = np.linspace(0,1,M)#アンテナ毎のポイント
filan = 0.5-0.5*np.cos(2*np.pi*theta)#空間方向にHanning window
fildis = 0.5-0.5*np.cos(2*np.pi*distance/N)#時間方向にHanning window
f, a = np.meshgrid(fildis, filan) #縦横メッシュデータを作成
filterdata = f*a #アンテナ方向と距離方向の重みを合成

#空間フィルタリング
filtereddata= filterdata*Reconstructed_signal

fftdata = np.fft.fft2(filtereddata) #2次元FFT
absdata = abs(fftdata)#振幅計算
magdata = 20*np.log10(absdata)#dBに変換
posdata, negadata = np.array_split(magdata, 2, 1)#ベースバンドを正の周波数と負の周波数に分割
leftdata, rightdata = np.array_split(posdata, 2)#左右に分割
mapdata = np.vstack([rightdata, leftdata])#タイリングでFFTの折り返しを無くす

fig9 = plt.figure(9)
ax = fig9.add_subplot(projection='3d')
print("\nCheck size of x1:", x1.shape)
ax.plot_surface(x1,y1,mapdata,cmap="jet")#レーダ画像
ax.set_title("符号化レーダーの2次元画像") #グラフタイトルを設定
ax.set_xlabel("x座標(m)",color="black")#軸ラベル
ax.set_ylabel("y座標(m)",color="black")
ax.set_zlabel("信号強度",color="black")
plt.savefig("./Fig9.png") #図の保存
plt.figaspect(1)

#描画
plt.show()
