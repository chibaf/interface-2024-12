""" クオータニオンの演算ライブラリ(python版)

Interface 2024年12月号付録

============
概要
============
本誌オリジナルのクオータニオンの基本演算ライブラリです。
演算効率よりも、原理式に忠実に実装していて、分かりやすさを重視しています。
同じインターフェースを持つ Arduino C++版も姉妹ライブラリとして別途提供します。
PC 上では python 版を使い、マイコン上では C++ 版と、移植しやすくなっています。

============
提供API関数
============
def innerProduct(a, b)-> float
    ベクトル内積
def outerProduct(a, b)-> tuple
    3D ベクトル外積
def crossAngle(a, b)-> float
    2つのベクトルの成す角

class Quaternion
    クオータニオン演算クラス
    メソッド内訳は class Quaternion の docstring を参照

============
使用例
============
from cq_quaternion import *

# q = 0.1+0.3i-0.2j-0.8k
q = Quaternion(0.1, 0.3, -0.2, -0.8)
# 単位クオータニオン化
q.normalize()
# 機体座標系(1,3,-0.4) をクオータニオン回転し、基準座標系に変換
vec = q.rotation((1,3,-0.4))
print('x,y,z = {}, {}, {}'.format(vec[0], vec[1], vec[2]))
# オイラー角
eul = q.getEuler()
print('Roll={}, Pitch={}, Yaw={} [rad]'.format(eul[0],eul[1],eul[2]))

============
免責
============
(1)プログラムやデータの使用により，使用者に損失が生じたとしても，著作権者とＣＱ出版(株)は，その責任を負いません．
(2)プログラムやデータにバグや欠陥があったとしても，著作権者とＣＱ出版(株)は，修正や改良の義務を負いません．
"""
import math

def innerProduct(a, b)-> float:
    """ベクトル内積 a * b

    Parameters
    -----
    a: array like 3要素のアレイライク (x,y,z)
    b: array like 3要素のアレイライク (x,y,z)

    Returns
    -----
    int or float
    """
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

def outerProduct(a, b)-> tuple:
    """ベクトル外積 a x b

    Parameters
    -----
    a: array like 3要素のアレイライク (x,y,z)
    b: array like 3要素のアレイライク (x,y,z)

    Returns
    -----
    tuple 3要素のタプル (x,y,z)
    """
    return (a[1] * b[2] - b[1] * a[2], b[0] * a[2] - a[0] * b[2], a[0] * b[1] - b[0] * a[1])

def crossAngle(a, b)-> float:
    """2つのベクトルの成す角

    Parameters
    -----
    a: array like 3要素のアレイライク (x,y,z)
    b: array like 3要素のアレイライク (x,y,z)

    Returns
    -----
    float 2つのベクトルの成す角 (0～PI) [rad]
    """
    try:
        theta = math.acos((a[0]*b[0]+a[1]*b[1]+a[2]*b[2]) / math.sqrt((a[0]*a[0]+a[1]*a[1]+a[2]*a[2])*(b[0]*b[0]+b[1]*b[1]+b[2]*b[2])))
    except:
        theta = 0
    return theta

class Quaternion():
    """回転を表現するクオータニオン

    右手座標系とし、回転角は右ねじ方向を正の方向とする。
    機体座標系から、基準座標系への変換をするクオータニオンを前提とする。

    実数部  : _r
    虚数部i : _i
    虚数部j : _j
    虚数部k : _k

    提供演算子
    -----
    2項演算子 + - * (演算対象は int or float or Quaternion型 or 4要素アレイライク型)
    単項演算子 + -
    複合演算子 += -= *=
    配列形式、スライスも可能 [] (インデックス0=実数部, 1=虚数部i, 2=虚数部j, 3=虚数部k)

    提供メソッド
    -----
    setValue(r:float, i:float, j:float, k:float)
        クオータニオン直値設定
    getValue()
        クオータニオン直値取得
    setRotate(vec, radian:float)
        回転軸ベクトルと回転角からクオータニオン設定
    getRotate()
        回転のクオータニオンと見なして、回転軸単位ベクトルと回転角を取得
    normalize(change_self:bool=True)
        単位クオータニオン化
    abs()
        norm値取得
    conj(change_self:bool=True)
        共役クオータニオン化
    rotation(vec)
        クオータニオンを適用してベクトル回転
    integralAngleVelocity(w, dt:float)
        機体座標(センサ座標)での角速度からクオータニオン積算
    getEuler()
        クオータニオンをオイラー角に変換
    """
    def __init__(self, r:float=1, i:float=0, j:float=0, k:float=0):
        self._r = r
        self._i = i
        self._j = j
        self._k = k

    def __pos__(self):
        return Quaternion(self._r, self._i, self._j, self._k)
    
    def __neg__(self):
        return Quaternion(-self._r, -self._i, -self._j, -self._k)

    def __abs__(self):
        return math.sqrt(self._r*self._r+self._i*self._i+self._j*self._j+self._k*self._k)

    def __add__(self, op):
        if isinstance(op, Quaternion):
            return Quaternion(self._r+op._r, self._i+op._i, self._j+op._j, self._k+op._k)
        elif isinstance(op, (float, int)):
            return Quaternion(self._r+op, self._i, self._j, self._k)
        else:   # 要素4 のアレイライク
            return Quaternion(self._r+op[0], self._i+op[1], self._j+op[2], self._k+op[3])
    
    def __sub__(self, op):
        if isinstance(op, Quaternion):
            return Quaternion(self._r-op._r, self._i-op._i, self._j-op._j, self._k-op._k)
        elif isinstance(op, (float, int)):
            return Quaternion(self._r-op, self._i, self._j, self._k)
        else:   # 要素4 のアレイライク
            return Quaternion(self._r-op[0], self._i-op[1], self._j-op[2], self._k-op[3])

    def __iadd__(self, op):
        if isinstance(op, Quaternion):
            self._r += op._r
            self._i += op._i
            self._j += op._j
            self._k += op._k
        elif isinstance(op, (float, int)):
            self._r += op
        else:   # 要素4 のアレイライク
            self._r += op[0]
            self._i += op[1]
            self._j += op[2]
            self._k += op[3]
        return self
    
    def __isub__(self, op):
        if isinstance(op, Quaternion):
            self._r -= op._r
            self._i -= op._i
            self._j -= op._j
            self._k -= op._k
        elif isinstance(op, (float, int)):
            self._r -= op
        else:   # 要素4 のアレイライク
            self._r -= op[0]
            self._i -= op[1]
            self._j -= op[2]
            self._k -= op[3]
        return self

    def __mul__(self, op):
        if isinstance(op, Quaternion):
            r = op._r
            i = op._i
            j = op._j
            k = op._k
        elif isinstance(op, (float, int)):
            r = op
            i = 0.0
            j = 0.0
            k = 0.0
        else:   # 要素4 のアレイライク
            r = op[0]
            i = op[1]
            j = op[2]
            k = op[3]
        rval = self._r*r - self._i*i - self._j*j - self._k*k
        ival = self._i*r + self._r*i - self._k*j + self._j*k
        jval = self._j*r + self._k*i + self._r*j - self._i*k
        kval = self._k*r - self._j*i + self._i*j + self._r*k
        return Quaternion(rval, ival, jval, kval)

    def __imul__(self, op):
        if isinstance(op, Quaternion):
            r = op._r
            i = op._i
            j = op._j
            k = op._k
        elif isinstance(op, (float, int)):
            r = op
            i = 0.0
            j = 0.0
            k = 0.0
        else:   # 要素4 のアレイライク
            r = op[0]
            i = op[1]
            j = op[2]
            k = op[3]
        rval = self._r*r - self._i*i - self._j*j - self._k*k
        ival = self._i*r + self._r*i - self._k*j + self._j*k
        jval = self._j*r + self._k*i + self._r*j - self._i*k
        kval = self._k*r - self._j*i + self._i*j + self._r*k
        self._r = rval
        self._i = ival
        self._j = jval
        self._k = kval
        return self

    def __getitem__(self, key):
        """配列形式の取得
        [0]:実数部r, [1]:虚数部i, [2]:虚数部j, [3]:虚数部k
        スライスも使用可能でタプル型が返る ex. [1:]:(虚数i部, j, k)
        """
        return (self._r, self._i, self._j, self._k)[key]

    def __setitem__(self, key, val):
        """配列形式の設定
        [0]:実数部r, [1]:虚数部i, [2]:虚数部j, [3]:虚数部k
        スライスも使用可能
        """
        if isinstance(key, slice):
            dummy = [None]*4
            dummy[key] = val
            for i in range(4):
                if dummy[i] is None:
                    continue
                if i == 0:
                    self._r = dummy[i]
                elif i == 1:
                    self._i = dummy[i]
                elif i == 2:
                    self._j = dummy[i]
                elif i == 3:
                    self._k = dummy[i]
        else:
            if key == 0:
                self._r = val
            elif key == 1:
                self._i = val
            elif key == 2:
                self._j = val
            elif key == 3:
                self._k = val

    def __repr__(self):
        return "{}, i: {}, j: {}, k: {}".format(self._r, self._i, self._j, self._k)

    def setValue(self, r:float, i:float, j:float, k:float)-> 'Quaternion':
        """クオータニオン直値設定

        Parameters
        -----
        r: float  実数部
        i: float  虚数部i
        j: float  虚数部j
        k: float  虚数部k

        Returns
        -----
        self
        """
        self._r = r
        self._i = i
        self._j = j
        self._k = k
        return self

    def getValue(self)-> tuple:
        """クオータニオン直値取得

        Returns
        -----
        tuple
            4要素のタプル (実数部, 虚数部i, 虚数部j, 虚数部k)
        """
        return (self._r, self._i, self._j, self._k)

    def setRotate(self, vec, radian:float)-> 'Quaternion':
        """回転軸ベクトルと回転角からクオータニオン設定
        
        Parameters
        -----
        vec: array like
            回転軸ベクトル 3要素のアレイライク [x, y, z] 単位ベクトル化して計算される
        radian: float
            回転角 [rad]
        
        Returns
        -----
        self
        """
        norm = math.sqrt(vec[0]*vec[0]+vec[1]*vec[1]+vec[2]*vec[2])
        self._r = math.cos(radian/2)
        sin_value = math.sin(radian/2) / norm
        self._i = sin_value * vec[0]
        self._j = sin_value * vec[1]
        self._k = sin_value * vec[2]
        return self

    def getRotate(self)-> tuple:
        """回転のクオータニオンと見なして、回転軸単位ベクトルと回転角を取得

        自身のクオータニオンを単位クオータニオン化して、同クオータニオンが示す
        回転軸単位ベクトルと、回転角を取得する

        Returns
        -----
        (tuple, float)
            第一要素は 3要素のタプルで、回転軸単位ベクトル (x, y, z)
            第二要素は 回転角[rad] (-PI to +PI)
        """
        temp = self.normalize(False)
        theta = math.acos(temp._r)*2
        sin_value = math.sin(theta/2)
        if sin_value < 1e-6:
            return ((1,0,0), 0)
        vec_x = temp._i / sin_value
        vec_y = temp._j / sin_value
        vec_z = temp._k / sin_value
        if theta > math.pi:
            return ((vec_x, vec_y, vec_z), theta-2*math.pi)
        else:
            return ((vec_x, vec_y, vec_z), theta)

    def normalize(self, change_self:bool=True)-> 'Quaternion':
        """単位クオータニオン化
        
        Parameters
        -----
        change_self: bool , default True
            自身の値を更新するか?

        Returns
        -----
        Quaternion 単位化されたクオータニオン
        """
        norm = math.sqrt(self._r**2+self._i**2+self._j**2+self._k**2)
        if norm < 1e-6:
            if change_self:
                self._r = 1.0
                self._i = 0.0
                self._j = 0.0
                self._k = 0.0
                return self
            else:
                return Quaternion()
        elif change_self:
            self._r /= norm
            self._i /= norm
            self._j /= norm
            self._k /= norm
            return self
        else:
            return Quaternion(self._r/norm, self._i/norm, self._j/norm, self._k/norm)

    def abs(self)-> float:
        """norm値取得

        Returns
        -----
        float norm値
        """
        return math.sqrt(self._r*self._r+self._i*self._i+self._j*self._j+self._k*self._k)

    def conj(self, change_self:bool=True)-> 'Quaternion':
        """共役クオータニオン化
        
        Parameters
        -----
        change_self: bool , default True
            自身の値を更新するか?

        Returns
        -----
        Quaternion 共役クオータニオン
        """
        if change_self:
            self._i *= -1
            self._j *= -1
            self._k *= -1
            return self
        else:
            return Quaternion(self._r, -self._i, -self._j, -self._k)

    def rotation(self, vec)-> tuple:
        """クオータニオンを適用してベクトル回転

        本オブジェクトのクオータニオンにより、機体座標系から基準座標系に座標変換をする。
        単位クオータニオンでないと、ベクトル長がスケーリングされる。

        Parameters
        -----
        vec: array like 機体座標系のベクトル3要素 (x座標, y座標, z座標)

        Returns
        -----
        tuple: 標準座標系のベクトル3要素 (x座標, y座標, z座標)
        """
        if isinstance(vec, Quaternion):
            q = self * vec * self.conj(False)
        else:
            q = self * Quaternion(0, vec[0], vec[1], vec[2]) * self.conj(False)
        return (q._i, q._j, q._k)

    def integralAngleVelocity(self, w, dt:float)-> 'Quaternion':
        """機体座標(センサ座標)での角速度からクオータニオン積算
        
        各時刻の3軸角速度から、機体座標から基準座標へ変換するクオータニオン内部値を更新する。
        基準座標は、本メソッド呼び出し前の初期クオータニオン値で定義される。
        初期機体座標 = 基準座標の場合は、初回 Quaternion(1., 0., 0., 0.) としておく。
        各時刻毎に本メソッドを呼び出し、積算更新してゆく。

        Parameters
        -----
        w: array like 機体座標系で観測される角速度3要素 (x軸角速度, y軸角速度, z軸角速度) [rad/sec]
        dt: float 1データ周期時間 [sec]

        Returns
        -----
        Quaternion 機体座標から基準座標へ変換するクオータニオン
        """
        rval = 0.5*(              - w[0]*self._i - w[1]*self._j - w[2]*self._k)*dt
        ival = 0.5*( w[0]*self._r                + w[2]*self._j - w[1]*self._k)*dt
        jval = 0.5*( w[1]*self._r - w[2]*self._i                + w[0]*self._k)*dt
        kval = 0.5*( w[2]*self._r + w[1]*self._i - w[0]*self._j)*dt
        self._r += rval
        self._i += ival
        self._j += jval
        self._k += kval
        self.normalize(True)
        return self

    def getEuler(self)-> tuple:
        """クオータニオンをオイラー角に変換

        機体座標系から、基準座標系に変換するクオータニオンとみなす。
        基準座標系を Z-Y-X の順で内因性(intrinsic)回転させて、機体座標系とした場合のオイラー角のラジアン値。
        単位クオータニオンでない場合は、単位化したクオータニオンを元に変換する。
        ジンバルロック時は(ピッチ角 +PI/2 or -PI/2)、ヨー角を 0 とする。

        Returns
        -----
        tuple: タプル3要素 (ロール角, ピッチ角, ヨー角)
        """
        norm2 = self._r*self._r+self._i*self._i+self._j*self._j+self._k*self._k
        if norm2 < 1e-12:
            return (0, 0, 0)
        sy = (self._r*self._j - self._i * self._k)*2
        if abs(norm2-1) > 1e-6:
            sy /= norm2
        if sy > 1-1e-6:
            y = math.pi/2
            sx = (self._i*self._j - self._r*self._k)*2
            cx = self._r*self._r - self._i*self._i + self._j*self._j - self._k*self._k
            z = 0
            x = math.atan2(sx, cx)
        elif sy < -1+1e-6:
            y = -math.pi/2
            sx = (self._r*self._k - self._i*self._j)*2
            cx = self._r*self._r - self._i*self._i + self._j*self._j - self._k*self._k
            z = 0
            x = math.atan2(sx, cx)
        else:
            y = math.asin(sy)
            x = math.atan2((self._j*self._k + self._r*self._i)*2, self._r*self._r - self._i*self._i - self._j*self._j + self._k*self._k)
            z = math.atan2((self._i*self._j + self._r*self._k)*2, self._r*self._r + self._i*self._i - self._j*self._j - self._k*self._k)
        return (x, y, z)
