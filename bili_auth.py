import log
import qrcode
import requests, json, os

logger = log.logger

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
        error_correction=qrcode.constants.ERROR_CORRECT_L,
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
    img.save("login.png")
    return loginInfo["data"]["qrcode_key"]

def login(loginInfo):
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

    config["login"] = True

    with open("config.json", "w+", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
    return True