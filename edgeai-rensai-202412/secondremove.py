from rembg import remove
from PIL import Image
import os

# 入力フォルダ
input_path = "./tmp1"
# 出力フォルダ
output_path = "./tmp2"

# 入力フォルダからファイル名を取得
all_files = os.listdir(input_path)
#特定の拡張子のファイルのみを取り出す
files = [i for i in all_files if i.endswith('.jpg') == True]

for file_name in files:
    input = Image.open(input_path + '/' + file_name)

    # 画像を切り抜く
    xp = 50
    yp = 50
    img_roi = input.crop((xp, yp, xp+300, yp+300)) # (left, upper, right, lower)

    output = remove(img_roi)

    # ファイル名抽出
    file_name_1 = file_name.split('.')[0]
 
    output.save(output_path + '/' + file_name_1 + '.png')
