import cv2
import os

# 入力フォルダ
input_saru = "./tmp2"
# 入力フォルダ
input_bg = "./tmp3"
# 出力フォルダ
output_path = "./tmp4"

# 入力フォルダからファイル名を取得
all_files = os.listdir(input_saru)
#特定の拡張子のファイルのみを取り出す
files = [i for i in all_files if i.endswith('.png') == True]

# 入力フォルダからファイル名を取得
all_files_bg = os.listdir(input_bg)
#特定の拡張子のファイルのみを取り出す
files_bg = [i for i in all_files_bg if i.endswith('.jpg') == True]

for file_name in files:
    frame_saru = cv2.imread(input_saru + '/' + file_name, cv2.IMREAD_UNCHANGED)  # アルファチャンネル込みで読み込む
    frame_saru = cv2.resize(frame_saru,None,fx=1.0,fy=1.0)

    # ファイル名抽出
    file_name_1 = file_name.split('.')[0]

    for file_name_bg in files_bg:
        # ファイル名抽出
        file_name_2 = file_name_bg.split('.')[0]
        frame_bg = cv2.imread(input_bg + '/' + file_name_2 + '.jpg')

        # 貼り付け先座標の設定
        xp = 100
        yp = 180
        x1, y1, x2, y2 = xp, yp, frame_saru.shape[1]+xp, frame_saru.shape[0]+yp

        # 合成
        frame_bg[y1:y2, x1:x2] = frame_bg[y1:y2, x1:x2] * (1 - frame_saru[:, :, 3:] / 255) + \
                      frame_saru[:, :, :3] * (frame_saru[:, :, 3:] / 255)

        cv2.imwrite(output_path + '/' + file_name_1 + '_' + file_name_2 + '.png', frame_bg)
