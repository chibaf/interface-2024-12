""" BLE Nordic UART サービスの送受信ライブラリ(python版)

Interface 2024年12月号付録

============
概要
============
BLEデバイスとの接続、データ送受信を制御するライブラリです。
python の非同期ライブラリ asyncio の下、動作します。

============
依存ライブラリ
============
マルチプラットフォームで BLE デバイスを制御する bleak ライブラリを使用します。
https://github.com/hbldh/bleak

事前に、bleak ライブラリをインストールします。
(コマンド例 : pip install bleak)

============
使用例
============
from BleUart import BleUartClient

async def main_loop():
    # 接続するデバイス名を指定
    client = BleUartClient("DEV_NAME")
    # BLEデバイスからPC に送られるデータは、asyncio.Queue で受信する
    receive_queue = client.get_queue()
    # 接続する
    await client.connect()
    # BLEデバイスにデータを送信する(20byte以内)
    await client.write(b'hello')
    # BLEデバイスからの受信データを待ち受ける(bytes型)
    message = await receive_queue.get()
    print(message.decode())
    # 最後に接続断
    await client.disconnect()

# start program
asyncio.run(main_loop())

============
免責
============
(1)プログラムやデータの使用により，使用者に損失が生じたとしても，著作権者とＣＱ出版(株)は，その責任を負いません．
(2)プログラムやデータにバグや欠陥があったとしても，著作権者とＣＱ出版(株)は，修正や改良の義務を負いません．
"""
import asyncio
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

# Nordic UART サービス UUID
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

class BleUartClient:

    async def _receive_data(self, _: BleakGATTCharacteristic, data: bytearray):
        await self._receive_queue.put(data)

    def __init__(self, device_name: str, address: str=""):
        """コンストラクタ

        parameters
        -----
        device_name: str
            接続するBLEデバイス名。connectメソッドで参照される。
        address: str, default=""
            接続するBLEアドレス。デフォルト空文字の場合、デバイス名からサーチされる。
        """
        self._target_address = ""
        self._target_client = None
        self._rx_char = None
        self._scan_sec = 6
        self._queue_size = 128
        self._dev_name = device_name
        self._receive_queue = asyncio.Queue(self._queue_size)
        if address:
            self._target_address = address

    async def connect(self, refresh: bool=True)-> bool:
        """BLE接続

        (注) 接続デバイスは、Nordic UART サービスを有していること
             接続遮断する場合は、最後に disconnect を呼び出すこと

        parameters
        -----
        refresh: bool, default=False
            False の場合、直前に自動サーチされた(又はコンストラクタ引数)BLEアドレスで接続
            True の場合、コンストラクタで指定したデバイス名で、新たにスキャンして接続
        
        returns
        -----
        bool
            True 接続成功, False 接続失敗
        """
        if self._target_client:
            return False
        # BLEアドレス指定され、refresh = False の場合、直接アドレス指定して接続
        if self._target_address and refresh is False:
            self._target_client = BleakClient(self._target_address)
            ack = await self._target_client.connect()
            if ack:
                await self._target_client.start_notify(UART_TX_CHAR_UUID, self._receive_data)
                nus = self._target_client.services.get_service(UART_SERVICE_UUID)
                self._rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)
            else:
                self._target_client = None
            return ack
        # 新たにスキャンしてデバイス捜索し、接続
        else:
            ble_device = await BleakScanner.find_device_by_name(self._dev_name, self._scan_sec)
            if ble_device:
                self._target_address = ble_device.address
                self._target_client = BleakClient(ble_device)
                ack = await self._target_client.connect()
                if ack:
                    await self._target_client.start_notify(UART_TX_CHAR_UUID, self._receive_data)
                    nus = self._target_client.services.get_service(UART_SERVICE_UUID)
                    self._rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)
                else:
                    self._target_client = None
                return ack
            else:
                return False

    def is_connected(self)-> bool:
        """BLE接続確認
        
        returns
        -----
        True: 接続中、False: 非接続
        """
        if self._target_client:
            return self._target_client.is_connected
        else:
            return False

    async def disconnect(self):
        """BLE接続断"""
        if self._target_client:
            await self._target_client.stop_notify(UART_TX_CHAR_UUID)
            await self._target_client.disconnect()
            self._target_client = None

    async def write(self, data: bytearray):
        """ペリフェラル(BLEサーバー)側にデータ送信
        
        parameters
        -----
        data: bytearray
            送信データ、バイナリアレイ型とする。最大サイズは、
            MTU - 3 = (デフォルト20) バイトとする。
        """
        if self._target_client:
            await self._target_client.write_gatt_char(self._rx_char, data, False)

    def get_queue(self):
        """ペリフェラル(BLEサーバー)側からのデータ受信キューを取得
        
        ペリフェラル側からのデータはキュー(asyncio.Queue)にスタックされる。
        本メソッドは、そのキューオブジェクトを取得する。

        returns
        -----
        asyncio.Queue
            深さ _queue_size のキュー。一回の受信データ(20byte以内)が、bytes型でスタックされる。
        """
        return self._receive_queue
