import cv2
import numpy as np
import albumentations as A

# 出力フォルダ
output_path = "./tmp1"

# 拡張枚数の設定
generate_img = 3
# データ拡張の拡張パイプラインを定義
img_size = 400

transform = A.Compose([
    # 反転（ランダム、確率50%）
    A.HorizontalFlip(p=0.5),
    # 回転（ランダム、確率100%）
    A.Rotate(limit=(-30, 30), p=1),
    # ランダム画像サイズ変更（スケーリング係数0.8～1.2、確率80%）
    A.RandomScale(scale_limit=(0.8, 1.2), p=0.8),
    # ランダムトリミングとリサイズ（リサイズ後のサイズ、トリミング領域、確率100%）
    A.RandomResizedCrop(height=img_size, width=img_size, scale=(1.0, 1.0), p=1)
])

img_path = "bgremoved.png"

# 画像をRGBに変換
img = cv2.imread(img_path, cv2.IMREAD_COLOR)

for i in range(generate_img):
    # データ拡張
    cropped_image = transform(image=img)['image']

    # 画像保存
    cv2.imwrite(output_path + '/' +  str(i) + '.jpg', cropped_image)
