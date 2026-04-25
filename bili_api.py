from functools import reduce
from hashlib import md5

import requests, json, os
import urllib.parse
import qrcode
import time
import log

logger = log.logger

mixinKeyEncTab = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]

def getMixinKey(orig: str):
    '对 imgKey 和 subKey 进行字符顺序打乱编码'
    return reduce(lambda s, i: s + orig[i], mixinKeyEncTab, '')[:32]

def encWbi(params: dict, img_key: str, sub_key: str):
    '为请求参数进行 wbi 签名'
    mixin_key = getMixinKey(img_key + sub_key)
    curr_time = round(time.time())
    params['wts'] = curr_time                                   # 添加 wts 字段
    params = dict(sorted(params.items()))                       # 按照 key 重排参数
    # 过滤 value 中的 "!'()*" 字符
    params = {
        k : ''.join(filter(lambda chr: chr not in "!'()*", str(v)))
        for k, v 
        in params.items()
    }
    query = urllib.parse.urlencode(params)                      # 序列化参数
    wbi_sign = md5((query + mixin_key).encode()).hexdigest()    # 计算 w_rid
    params['w_rid'] = wbi_sign
    return params

def getWbiKeys() -> tuple[str, str]:
    '获取最新的 img_key 和 sub_key'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Referer': 'https://www.bilibili.com/'
    }
    resp = requests.get('https://api.bilibili.com/x/web-interface/nav', headers=headers)
    resp.raise_for_status()
    json_content = resp.json()
    img_url: str = json_content['data']['wbi_img']['img_url']
    sub_url: str = json_content['data']['wbi_img']['sub_url']
    img_key = img_url.rsplit('/', 1)[1].split('.')[0]
    sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
    return img_key, sub_key

def wbi_sign():
    img_key, sub_key = getWbiKeys()

    signed_params = encWbi(
        params={
            'foo': '114',
            'bar': '514',
            'baz': 1919810
        },
        img_key=img_key,
        sub_key=sub_key
    )

    signed_params.pop("bar")
    signed_params.pop("baz")
    signed_params.pop("foo")

    # query = urllib.parse.urlencode(signed_params)

    return signed_params

class BiliPollError(Exception):
    """
    B站Web端扫码登录错误

    :param info: 扫码接口返回值
    """
    def __init__(self, info):
        self.info = info
        message = "扫码出现错误：" + info["data"]["message"]
        super().__init__(message)

def generate_qr_in_cmd(text):
    # 创建QRCode对象
    qr = qrcode.QRCode(
        version=1,
        error_correction=1,  # ERROR_CORRECT_L
        box_size=1,  # 控制二维码在终端中的大小
        border=1,
    )
    
    # 添加数据
    qr.add_data(text)
    qr.make(fit=True)
    
    # 生成二维码矩阵
    matrix = qr.get_matrix()
    
    # 清屏（Windows CMD）
    os.system('cls')
    
    # 打印二维码
    for row in matrix:
        line = ''
        for pixel in row:
            if pixel:
                line += '██'  # 黑色方块
            else:
                line += '  '  # 空白
        print(line)

def get_qrcode():
    """
    获取B站Web端扫码登录二维码

    :param path: 二维码保存路径，格式为: "path_时间戳.png"，例: "bili_qrcode_1743233445.png"
    :return: 扫码登录秘钥
    """

    loginInfo = requests.get(
        url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            }
        ).json()

    # 生成二维码
    generate_qr_in_cmd(loginInfo['data']['url'])
    img = qrcode.make(loginInfo['data']['url'])
    with open("login.png", "wb") as f:
        img.save(f)
    return loginInfo["data"]["qrcode_key"]

def get_buvid3():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/149.0"
    }

    response = requests.get(
        url = "https://api.bilibili.com/x/web-frontend/getbuvid",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        if data["code"] == 0:
            buvid3 = data["data"]["buvid"]
            return buvid3
        else:
            logger.error(f"获取buvid3失败，错误信息：{data['code']} {data['message']}")
    else:
        logger.error(f"获取buvid3失败，HTTP状态码：{response.status_code}")

    return False

def get_uname(mid):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/149.0"
    }

    params = {
        "mid": mid
    }
    
    response = requests.get(
        url = "https://api.bilibili.com/x/web-interface/card",
        headers=headers,
        params=params
    )

    if response.status_code == 200:
        data = response.json()
        if data["code"] == 0:
            uname = data["data"]["card"]["name"]
            return uname
        else:
            logger.error(f"获取用户昵称失败，错误信息：{data['code']} {data['message']}")
    else:
        logger.error(f"获取用户昵称失败，HTTP状态码：{response.status_code}")

    return False

def get_uid(room_id):
    url = "https://api.live.bilibili.com/room/v1/Room/get_info"
    params = {"room_id": room_id}
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }
    response = requests.get(url=url, params=params, headers=headers)
    try:
        data = response.json()
        if data["code"] != 0:
            raise RuntimeError(f"error code: {data}")
    except Exception as e:
        logger.error(f"获取uid失败: {e}")
        raise
    
    return data

def login(loginInfo):
    buvid3 = get_buvid3()

    if not buvid3:
        logger.error("获取buvid3失败，无法登录")
        return False

    response = requests.get(
        url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            },
        params = {"qrcode_key": loginInfo}
        )

    pollInfo = response.json()

    if pollInfo["data"]['code'] == 0:
        logger.info("登录成功")
    else:
        error = BiliPollError(pollInfo)
        return error

    cookies = response.cookies

    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    for cookie in cookies:
        config.setdefault(cookie.name, "")
        config[cookie.name] = cookie.value

    config["uname"] = get_uname(config["DedeUserID"])
    config["buvid3"] = buvid3

    with open("config.json", "w+", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

    return True