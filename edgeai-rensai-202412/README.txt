2024/10/11 Toshio Iwata wrote

インターフェース2024年12月号
生成AI×エッジデバイスでAI画像認識
連載1回目　ダウンロードアーカイブ

Google Colabにアップロードして次のように実行します。
（記事をよく読んで実行しましょう）

!pip install diffusers transformers accelerate	ツールのインストール

run list1-2.py					サル画像の生成

!pip install rembg				ツールのインストール

run thefirstremove.py				背景切り取り

mkdir tmp1					フォルダ作成
run changeshape.py				画像の加工

mkdir tmp2					フォルダ作成
run secondremove.py				背景切り取り（2回目）

mkdir tmp3					フォルダ生成
run generatebg.py				背景の生成

mkdir tmp4					フォルダ生成
run putnihonzaru.py				サル画像と背景の合成

記事通り進めればtmp4フォルダに9枚の画像が生成される。

Copyright (C) 2024　Toshio Iwata