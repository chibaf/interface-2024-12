from BleUart import BleUartClient
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

""" 6軸IMUデータを所定時間取得して、numpy形式のファイル保存

コンソール画面にキーボード入力が促されたら、何らかのキー入力する。
以後所定時間 (_TIMEOVER_SEC) [sec] の間 6軸IMU データを取得する。
最後に numpy形式の所定ファイル名 (_SAVE_FILE) に、データを保存する。

保存ファイルは、int16型で (サンプル点数, 6) サイズの2次元アレイ。

[:, 0] => x軸加速度バイナリ (-32768～+32767 が -2g～+2g に対応)
[:, 1] => y軸加速度バイナリ (-32768～+32767 が -2g～+2g に対応)
[:, 2] => z軸加速度バイナリ (-32768～+32767 が -2g～+2g に対応)
[:, 3] => x軸角速度バイナリ (-32768～+32767 が -250dps～+250dps に対応)
[:, 4] => y軸角速度バイナリ (-32768～+32767 が -250dps～+250dps に対応)
[:, 5] => z軸角速度バイナリ (-32768～+32767 が -250dps～+250dps に対応)
"""

_TIMEOVER_SEC = 10
_DEVICE_NAME = "IMU_BASE"
_SAVE_FILE = "sampling.npy"

async def ainput(prompt: str = "") -> str:
    """非同期でキーボード入力を待つ
    
    Parameters
    -----
    prompt: str
        コンソール上に表示されるプロンプト

    Returns
    -----
        改行キーまでに入力された文字
    """
    with ThreadPoolExecutor(1, "ainput") as executor:
        return await asyncio.get_event_loop().run_in_executor(executor, input, prompt)

async def main_loop():
    client = BleUartClient(_DEVICE_NAME)
    receive_queue = client.get_queue()
    await client.connect()
    if not client.is_connected():
        return

    data = b''
    key = await ainput("start ok? >>")  # なんらかのキー入力待ち
    await client.write(b'b')    # IMUデータ連続送信 ON
    start = time.time()
    # 所定時間の間の受信バイナリデータを累積
    while time.time() - start < _TIMEOVER_SEC:
        data += await receive_queue.get()
    await client.write(b'e')    # IMUデータ連続送信 OFF
    await client.disconnect()
    # バイナリデータ列は、符号付16bitリトルエンディアン形式なので、int16型に復元
    # 行列サイズを (サンプル点数) x 6 に変形
    #
    # M5Stack Atom S3 から PC に送られるデータは、notify データとして送られる。
    # 1回の notify データは、1回の IMUデータサンプリングに対応する 12byte 。
    # 12byte データは、符号付16bitリトルエンディアン形式。12byte は順に以下の通り、
    # acc_x(L) acc_x(H) acc_y(L) acc_y(H) acc_z(L) acc_z(H) gyr_x(L) gyr_x(H) gyr_y(L) gyr_y(H) gyr_z(L) gyr_z(H)
    #
    # arr_imu[:, 0] => x軸加速度バイナリ (-32768～+32767 が -2g～+2g に対応)
    # arr_imu[:, 1] => y軸加速度バイナリ (-32768～+32767 が -2g～+2g に対応)
    # arr_imu[:, 2] => z軸加速度バイナリ (-32768～+32767 が -2g～+2g に対応)
    # arr_imu[:, 3] => x軸角速度バイナリ (-32768～+32767 が -250dps～+250dps に対応)
    # arr_imu[:, 4] => y軸角速度バイナリ (-32768～+32767 が -250dps～+250dps に対応)
    # arr_imu[:, 5] => z軸角速度バイナリ (-32768～+32767 が -250dps～+250dps に対応)
    arr_imu = np.frombuffer(data, dtype=np.int16).reshape((-1,6))
    np.save(_SAVE_FILE, arr_imu)

asyncio.run(main_loop())