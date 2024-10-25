# Interface 2024年12月号
# 線形代数
# アダマール行列と相関計算
#　(c) 米本成人
#   August, 2024

#Google colabを利用する時は下の#を外して!pipでインストールすること
#!pip install japanize-matplotlib

import japanize_matplotlib#日本語用matplotlib
import numpy as np#数値計算用ライブラリ
import matplotlib.pyplot as plt#グラフ描画用ライブラリ
from mpl_toolkits.mplot3d import Axes3D      ### 3Dなら必要

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

    
#16次のアダマール行列を生成する
order = 16#行列の幅
H = hadamard_matrix(order)#関数呼び出し

# 行列のサイズを取得して表示する
print("Hadamard matrix H:")
print(H)

#データ描画
M = order
antenna = np.linspace(1,M,M)#アンテナ番号
bit_state = antenna#f符号長
x_mesh, y_mesh = np.meshgrid(antenna, bit_state)#アンテナ番号と符号列のビットに合わせたメッシュデータを作る

fig1 = plt.figure(1)
ax = fig1.add_subplot(projection='3d')
for i in range(x_mesh.shape[0]):
    ax.plot(x_mesh[M-i-1], y_mesh[M-i-1], H[M-i-1], label=f'Line {i+1}')#奥側の線から描画
plt.xticks([1,6,11,16])#x方向の目盛
plt.yticks([1,6,11,16])#y方向の目盛
ax.set_title("16次のアダマール符号") #グラフタイトルを設定
ax.set_xlabel("時間列", color="black")#軸ラベル
ax.set_ylabel("アンテナ番号",color="black")#軸ラベル
ax.set_zlabel("符号",color="black")
#ax.plot_surface(x_mesh, y_mesh, H ,cmap="jet")#3次元的な曲面を描く
plt.savefig("./Fig1.png") #図の保存


########
#符号の相関計算
########
I = H@np.transpose(H)#アダマール行列と転置行列との内積

# 行列のサイズを取得して表示する
print("I=H*H^T")
print(I)

fig2 = plt.figure(2)
ax = fig2.add_subplot(projection='3d')
ax.plot_surface(x_mesh, y_mesh, I,cmap="jet")#3次元的な曲面を描く
plt.xticks([1,6,11,16])#x方向の目盛
plt.yticks([1,6,11,16])#y方向の目盛
ax.set_title("符号の相互相関") #グラフタイトルを設定
ax.set_xlabel("元の符号の番号", color="black")#軸ラベル
ax.set_ylabel("相手の符号の番号",color="black")#軸ラベル
ax.set_zlabel("相関値",color="black")
plt.savefig("./Fig2.png") #図の保存

########
#クロックが一つずれた波形を作成して相関計算
########
S =np.roll(H, shift = 1, axis=1)#x方向に１つずらして回す
#元符号との相関値
J = S@H

# 行列のサイズを取得して表示する
print("Shifted Hadamard matrix \nS:")
print(S)
print("Inner product of shifted Hadamard matrix S*H\nJ:")
print(J)

#3Dグラフ化
fig3 = plt.figure(3)
ax = fig3.add_subplot(projection='3d')
ax.plot_surface(x_mesh, y_mesh, abs(J),cmap="jet")#3次元的な曲面を描く
plt.xticks([1,6,11,16])#x方向の目盛
plt.yticks([1,6,11,16])#y方向の目盛
ax.set_title("符号の相互相関") #グラフタイトルを設定
ax.set_xlabel("元の符号の番号", color="black")#軸ラベル
ax.set_ylabel("一つずらした符号の番号",color="black")#軸ラベル
ax.set_zlabel("相関値",color="black")
plt.savefig("./Fig3.png") #図の保存

#描画
plt.show()#figureの表示


