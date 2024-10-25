# Interface 2024年12月号
# 線形代数
# M系列、Gold系列符号の製作と相関計算
#　(c) 米本成人
#   August, 2024

#Google colabを利用する時は下の#を外して!pipでインストールすること
#!pip install japanize-matplotlib

import japanize_matplotlib#日本語用malolib
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D      ### 3Dなら必要

#M系列の定義
#bit演算を四則演算で実現
def generate_m_sequence(taps, seed, length):
    state = seed[:]#シフトレジスタを模擬したstateに初期値seedを入れる

    m_sequence = []#M系列の空き行列を作る
    
    for i in range(length):#length 分繰り替えす
        # 出力ビット（stateの最後の要素）を取得
        output = state[-1]#最後の要素を抜く
        #print(i, "th output", output)
        m_sequence.append(output)#最後の要素を出力として出す。
        
        # フィードバックビットを計算
        feedback = -1#戻り値の最初の値を入力１だと思ったが、タップする数の－の数が負の時に計算結果が＋になるように設定
  
        for tap in taps:#シフトレジスタのXORに入れるタップの場所に来たら、
            feedback = -state[tap - 1]*feedback #ビットだとXORだが、±１なので、掛け算で代用（同符号の時－、異符号の時＋となるように）
         
        # シフトしてフィードバックビットを最上位ビットにセット
        state = [feedback] + state[:-1]#stateの最初に計算結果を入れて、最初のstateを後ろにずらして付ける
    
    return m_sequence

def convert_zeros_to_negatives(sequence):
    return [-1 if bit == 0 else bit for bit in sequence]


# 例: 3ビットのLFSRを使用してM系列を生成
n=3#レジスタの数
taps = [3, 1]  # x^3 + x + 1 に対応するタップ位置
seed = [1, -1, -1]  # 初期状態
length = 2**n-1  # 生成する系列の長さ（2**n - 1 = 7）

#違う状態方程式に変えて異なるM系列を生成
# 例: 3ビットのLFSRを使用してM系列を生成
taps = [3,2]  # x^3 + x^2 + 1 に対応するタップ位置

# 1から7までの数値を2進数に変換して、1桁ずつ配列に格納
binary_arrays = []
H = []

N = 7#作成するM系列の数（最大2^n - 1 = 7）
for i in range(1, N+1):#,seed=0はうまく行かないので1から2^nまで

    # 2進数に変換し、'0b'の部分を取り除く
    binary_str = bin(i)[2:]
    
    # 各ビットを0と1の整数に変換してリストに格納
    binary_array = [int(bit) for bit in binary_str]
    
    # 4ビットで表現したい場合、例えば2ビットの場合はゼロパディング
    binary_array = [0] * (n - len(binary_array)) + binary_array  # 3ビットの場合

    binary_arrays.append(binary_array)

    seed = convert_zeros_to_negatives(binary_array)#バイナリ値の０を1に変換
    m_seq = generate_m_sequence(taps, seed, length)
    H.append(m_seq)

print("Seed:\n", binary_arrays)
print("H:")
for bit in H:
    print(bit)
    
#データ描画
seed= np.linspace(1,N,N)#アンテナ番号
length = np.linspace(1,length,length)#符号長

#3Dグラフ化
x_mesh, y_mesh = np.meshgrid(length,seed)#アンテナ番号と符号列のビットに合わせたメッシュデータを作る

fig4 = plt.figure(4)
ax = fig4.add_subplot(projection='3d')
for i in range(x_mesh.shape[0]):
    ax.plot(x_mesh[i], y_mesh[i], H[i], label=f'Line {i+1}')
ax.set_title("符号の時間的変化") #グラフタイトルを設定
ax.set_xlabel("時間列", color="black")
ax.set_ylabel("初期値",color="black")#軸ラベル
ax.set_zlabel("符号",color="black")
plt.savefig("./Fig4.png") #図の保存

#相関計算
I = np.transpose(H)
J = H@I
print("HH^T:\n",J)

#データ描画
#3Dグラフ化
seed= np.linspace(1,N,N)#符号番号
length = seed#符号長
x_mesh, y_mesh = np.meshgrid(length,seed)#アンテナ番号と符号列のビットに合わせたメッシュデータを作る
#3Dグラフ化
fig5 = plt.figure(5)
ax = fig5.add_subplot(projection='3d')
ax.set_title("符号の相互相関") #グラフタイトルを設定
ax.set_xlabel("符号を作った初期値", color="black")
ax.set_ylabel("符号を作った初期値",color="black")#軸ラベル
ax.set_zlabel("相関値",color="black")
ax.plot_surface(x_mesh, y_mesh, abs(J),cmap="jet")#3次元的な曲面を描く
plt.savefig("./Fig5.png") #図の保存

#
#Gold 符号
#

# 例: 2つの異なるM系列を生成
taps1 = [3, 2]  # x^3 + x^2 + 1 に対応するタップ位置
seed1 = [1, -1, -1]  # 初期状態
length = 7  # 生成する系列の長さ（2^n - 1 = 7）

taps2 = [3, 1]  # x^3 + x + 1 に対応するタップ位置
seed2 = [1, -1, -1]  # 初期状態

m_seq1 = np.array(generate_m_sequence(taps1, seed1, length))#1個目の方程式でM系列を生成
m_seq2 = np.array(generate_m_sequence(taps2, seed2, length))#2個目の方程式でM系列を生成
print("seed1:", seed1)
print("M系列1:", m_seq1)
print("seed2:", seed2)
print("M系列2:", m_seq2)

# Gold符号を生成 (M系列のXOR)
gold_code = m_seq1*m_seq2#２つのM系列を掛け算
print("Gold符号:", gold_code)

#描画
plt.show()



