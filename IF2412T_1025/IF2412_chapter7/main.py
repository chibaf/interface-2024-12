from typing import List
import csv
import numpy as np
from dataclasses import dataclass, field
from PIL import Image,ImageDraw

@dataclass
class Transform:
    """ オブジェクトの位置姿勢情報 """
    # 位置座標
    position:np.ndarray = field(default_factory=lambda: np.zeros(3))
    # XYZ順のオイラー角（単位はrad）
    euler_angle:np.ndarray = field(default_factory=lambda: np.zeros(3))
    # x,y,z各軸方向のスケール
    scale:np.ndarray = field(default_factory=lambda: np.array([1.0]*3))

    @property
    def trans_mat(self)->np.ndarray:
        """ 平行移動行列 """
        x, y, z = self.position
        return np.array([
            [1.0, 0.0, 0.0, x],
            [0.0, 1.0, 0.0, y],
            [0.0, 0.0, 1.0, z],
            [0.0, 0.0, 0.0, 1.0],
        ])

    @property
    def rot_mat(self)->np.ndarray:
        """ 回転移動行列 """
        rx, ry, rz = self.euler_angle
        # x軸を中心にrx回転する行列
        rx_mat = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, np.cos(rx), -np.sin(rx), 0.0],
            [0.0, np.sin(rx), np.cos(rx), 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])
        # y軸を中心にry回転する行列
        ry_mat = np.array([
            [np.cos(ry), 0.0, np.sin(ry), 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [-np.sin(ry), 0.0, np.cos(ry), 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])
        # z軸を中心にrz回転する行列
        rz_mat = np.array([
            [np.cos(rz), -np.sin(rz), 0.0, 0.0],
            [np.sin(rz), np.cos(rz), 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])
        # XYZ順にかけた回転行列
        return rz_mat @ ry_mat @ rx_mat

    @property
    def scale_mat(self)->np.ndarray:
        """ 拡縮行列 """
        sx, sy, sz = self.scale
        return np.array([
            [sx, 0.0, 0.0, 0.0],
            [0.0, sy, 0.0, 0.0],
            [0.0, 0.0, sz, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])

    @property
    def right(self)->np.ndarray:
        """ 右ベクトル """
        return (self.rot_mat @ np.append(Transform.RIGHT(), 1.0))[:3]

    @property
    def up(self)->np.ndarray:
        """ 上ベクトル """
        return (self.rot_mat @ np.append(Transform.UP(), 1.0))[:3]

    @property
    def forward(self)->np.ndarray:
        """ 前ベクトル """
        return (self.rot_mat @ np.append(Transform.FORWARD(), 1.0))[:3]

    @staticmethod
    def RIGHT()->np.ndarray:
        """ 右方向の定義 """
        return np.array([1.0, 0.0, 0.0])

    @staticmethod
    def UP()->np.ndarray:
        """ 上方向の定義 """
        return np.array([0.0, 0.0, 1.0])

    @staticmethod
    def FORWARD()->np.ndarray:
        """ 前方向の定義 """
        return np.array([0.0, 1.0, 0.0])


@dataclass
class PointCloudObject:
    """ 点群オブジェクト """
    # 点群オブジェクトの位置・姿勢情報
    transform:Transform = field(default_factory=lambda: Transform())
    # 頂点情報
    vertices:List[np.ndarray] = field(default_factory=lambda: [])

    @property
    def model_mat(self)->np.ndarray:
        """ モデル行列 """
        return self.transform.trans_mat @ self.transform.rot_mat @ self.transform.scale_mat


@dataclass
class CameraInfo:
    """ カメラ情報 """
    # カメラの位置・姿勢情報
    transform:Transform = field(default_factory=lambda: Transform())
    # 投影モード（0:平行投影、1:透視投影）
    projection_mode:int = 0
    # 透視投影時の画面横方向の画角（単位はrad）
    fov_horizontal:float = np.pi/3
    # 平行投影時のカメラのイメージセンサーの横幅
    view_horizontal:float = 10.0
    # ニアクリップ
    near_clip:float = 0.1
    # ファークリップ
    far_clip:float = 1e3

    def view_vertical(self, aspect_ratio:float)->float:
        """ 平行投影時のカメラのイメージセンサーの縦幅 """
        return self.view_horizontal / aspect_ratio

    def fov_vertical(self, aspect_ratio:float)->float:
        """ 透視投影時の画面縦方向の画角（単位はrad） """
        return np.arctan(np.tan(self.fov_horizontal/2.0)/aspect_ratio)*2.0

    @property
    def view_mat(self)->np.ndarray:
        """ ビュー行列 """
        # カメラのTR行列の逆行列
        return np.linalg.inv(self.transform.trans_mat @ self.transform.rot_mat)

    def projection_mat(self, aspect_ratio:float)->np.ndarray:
        """ プロジェクション行列 """
        # 今回はカメラのX方向を右、Z方向を上、Y方向を前と定義する
        if self.projection_mode == 0:
            # 平行投影の場合
            return np.array([
                [2/self.view_horizontal, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 2/self.view_vertical(aspect_ratio), 0.0],
                [0.0, 0.0, 0.0, 1.0]
            ])
        else:
            # 透視投影の場合
            near_far_mat = (
                # y=farクリップの距離がy=1となるように変換する行列
                np.array([
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1/(self.far_clip-self.near_clip), 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ])
                # y=ニアクリップの距離がy=0になるように移動する行列
                @ np.array([
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, -self.near_clip],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ])
            )
            cot = lambda val: 1.0/np.tan(val)
            p2 = near_far_mat @ np.array([
                [cot(self.fov_horizontal/2), 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, cot(self.fov_vertical(aspect_ratio)/2), 0.0],
                [0.0, 0.0, 0.0, 1.0]
            ])
            p2[3, 1] = 1.0
            p2[3, 3] = 0.0
            return p2


def read_point_cloud_data(path:str)->PointCloudObject:
    """ 点群データの読み込み
    Args:
        path (str): 点群CSVのパス
    Returns:
        PointCloudObject: 点群オブジェクト
    """
    point_cloud = PointCloudObject()
    with open(path, mode='r', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0].startswith("#"):
                # コメント行を読み飛ばす
                continue
            if len(row) < 2:
                continue
            key = row[0].strip()
            if key == "$POS":
                point_cloud.transform.position[0] = float(row[1])
                point_cloud.transform.position[1] = float(row[2])
                point_cloud.transform.position[2] = float(row[3])
            elif key == "$ROT":
                point_cloud.transform.euler_angle[0] = np.deg2rad(float(row[1]))
                point_cloud.transform.euler_angle[1] = np.deg2rad(float(row[2]))
                point_cloud.transform.euler_angle[2] = np.deg2rad(float(row[3]))
            elif key == "$SCALE":
                point_cloud.transform.scale[0] = float(row[1])
                point_cloud.transform.scale[1] = float(row[2])
                point_cloud.transform.scale[2] = float(row[3])
            elif len(row) == 3:
                point = np.array([float(row[0]), float(row[1]), float(row[2])])
                point_cloud.vertices.append(point)
    return point_cloud

def read_camera_info(path:str)->CameraInfo:
    """ カメラ情報の読み込み
    Args:
        path (str): カメラ情報CSVのパス
    Returns:
        CameraInfo: カメラ情報
    """
    camera_info = CameraInfo()
    with open(path, mode='r', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0].startswith("#"):
                # コメント行を読み飛ばす
                continue
            if len(row) < 2:
                continue
            key = row[0].strip()
            if key == "$POS":
                camera_info.transform.position[0] = float(row[1])
                camera_info.transform.position[1] = float(row[2])
                camera_info.transform.position[2] = float(row[3])
            elif key == "$ROT":
                camera_info.transform.euler_angle[0] = np.deg2rad(float(row[1]))
                camera_info.transform.euler_angle[1] = np.deg2rad(float(row[2]))
                camera_info.transform.euler_angle[2] = np.deg2rad(float(row[3]))
            elif key == "$PROJ":
                camera_info.projection_mode = int(row[1])
            elif key == "$FOV":
                camera_info.fov_horizontal = np.deg2rad(float(row[1]))
            elif key == "$VIEW":
                camera_info.view_horizontal = float(row[1])
            elif key == "$NEAR":
                camera_info.near_clip = float(row[1])
            elif key == "$FAR":
                camera_info.far_clip = float(row[1])
    return camera_info

def viewport_mat(img_width:int, img_height:int)->np.ndarray:
    """ ビューポート行列 """
    # 今回はカメラのX方向を右、Z方向を上と定義する
    return np.array([
        [img_width/2, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, img_height/2, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ]) @ np.array([
        [1.0, 0.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 1.0],
        [0.0, 0.0, 0.0, 1.0],
    ])

def rendering(camera_info:CameraInfo, objects:List[PointCloudObject], img_width:int=640, img_height:int=360)->Image:
    """ カメラ情報と点群情報から画像をレンダリングする
    Args:
        camera_info (CameraInfo): カメラ情報
        objects (List[PointCloudObject]): 描画対象の点群情報
        img_width (int, optional): 出力画像サイズ横幅. Defaults to 640.
        img_height (int, optional): 出力画像サイズ縦幅. Defaults to 360.
    Returns:
        Image: レンダリング画像
    """
    aspect_ratio = img_width/img_height

    # ジオメトリ変換
    points_at_clip = []
    V = camera_info.view_mat
    P = camera_info.projection_mat(aspect_ratio)
    for obj in objects:
        M = obj.model_mat
        # 各頂点をMVP変換する
        mvp_mat = P @ V @ M
        for point in obj.vertices:
            # クリップ座標系上に投影した頂点
            point_at_clip = mvp_mat @ np.append(point, 1.0)
            # 透視投影の場合は透視除算
            if camera_info.projection_mode == 1:
                point_at_clip[0] /= point_at_clip[3]
                point_at_clip[2] /= point_at_clip[3]
                point_at_clip[3] /= point_at_clip[3]
            # カメラより前方かつクリッピング範囲内の頂点のみ採用
            if(
                -1 <= point_at_clip[0] < 1 and
                -1 <= point_at_clip[2] < 1 and
                0 < point_at_clip[1]
            ):
                points_at_clip.append(point_at_clip)

    # ビューポート変換
    points_at_screen = []
    VP = viewport_mat(img_width, img_height)
    for point_at_clip in points_at_clip:
        # スクリーン座標系上に投影した頂点
        point_at_screen = VP @ point_at_clip
        points_at_screen.append(point_at_screen)

    # 全画素黒色の画像の作成
    img = Image.new("RGB", (img_width, img_height), (0,0,0))
    for point_at_screen in points_at_screen:
        # 頂点が投影されるピクセルを白で描画
        x_pix = int(point_at_screen[0])
        y_pix = img_height - 1 - int(point_at_screen[2])
        img.putpixel((x_pix, y_pix), (255, 255, 255))

    return img

if __name__ == "__main__":
    # サンプルデータのパス
    point_cloud_path = "data.csv"
    camera_info_path = "camera.csv"
    # カメラ情報CSVファイルの読込
    camera_info = read_camera_info(camera_info_path)
    # 点群情報CSVファイルの読み込み
    point_cloud = read_point_cloud_data(point_cloud_path)
    # 読み込んだカメラ情報と点群情報でレンダリングを実行
    img = rendering(camera_info, [point_cloud])
    # レンダリングされた画像を表示
    img.save("img.png")