# coding=utf-8
import log
import random
import bili_api
import traceback
import sys, os, json, requests, time

currentVersion = "1.3.2"
frontSpace = (51 - len(currentVersion)) * " "
logger = log.logger


# 全局异常处理钩子
def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("未知错误！", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception

if not os.path.exists("config.json"):
    config = {"login": False, "room_id": 0}
    with open("config.json", "w+", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


# 登录B站
def login_bilibili():
    loginInfo = bili_api.get_qrcode()
    input(
        f"如无法加载二维码可打开 {os.getcwd()}\\login.png 扫码登录\n确认登录后请按任意键继续..."
    )
    status = bili_api.login(loginInfo)
    if status == True:
        time.sleep(1)
        main()
    else:
        logger.error(status)
        input("按任意键继续...")
        main()


def get_roomid():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    room_id = input("请输入房间号：")
    if room_id != "":
        config["room_id"] = room_id
        with open("config.json", "w+", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    else:
        logger.error("房间号错误！")
        input("按任意键继续...")

    main()


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
        input("按任意键继续...")
        raise

    return data


# 辣条礼物函数
def send_latiao(num):
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    url = "https://api.live.bilibili.com/gift/v2/gift/send"
    room_info = get_uid(config["room_id"])
    data = {
        "gift_id": 1,  # 辣条编号为1
        "gift_num": num,  # 数量
        "ruid": room_info["data"]["uid"],  # 主播uid
        "coin_type": "silver",  # 银瓜子
        "biz_id": config["room_id"],
        "csrf": config[
            "bili_jct"
        ],  # 跨站请求伪造,捕获方法为任意直播间发一条消息,在network中捕获send?开头的fetch信息
        "csrf_token": config["bili_jct"],  # 跨站请求伪造token
    }
    headers = {
        "Cookie": f'SESSDATA={config["SESSDATA"]}; bili_jct={config["bili_jct"]}',
        "Origin": "https//live.bilibili.com",
        "Referer": f'https://live.bilibili.com/{config["room_id"]}',
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    }
    response = requests.post(url=url, data=data, headers=headers)
    response.encoding = "utf-8"
    if response.status_code == 200:
        response = response.json()
        if response["code"] == 0:
            logger.info(
                f'{response["data"]["uname"]} 在 {room_info["data"]["room_id"]} {response["data"]["gift_action"]} {response["data"]["gift_num"]} 个 {response["data"]["gift_name"]}'
            )
        else:
            logger.info(response["msg"])
    else:
        logger.error(
            f'Send latiao to {config["room_id"]} failed.Status code: {response.status_code}'
        )


# 辣条赠送循环函数
def manual_send_latiao(loop=False):
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    if not config["login"]:
        select = input("未登录B站账号，是否登录？(Y/n)")
        if select in ["y", "Y", ""]:
            login_bilibili()
        else:
            main()

    if config["room_id"] == 0:
        get_roomid()

    num = int(input("Number:"))

    if not loop:
        send_latiao(num)
        time.sleep(3)
        main()
    else:
        while True:
            if num > 0:
                send_latiao(1)
                num -= 1
            else:
                time.sleep(3)
                main()


def like_mode():
    mode = input(
        """请选择点赞模式:
1.一次性点满
2.模拟点赞
3.返回主菜单
请选择:"""
    )

    if mode == "1":
        like_report(True)
    elif mode == "2":
        like_report(False)
    elif mode == "3":
        main()
    else:
        input("输入有误，按回车键重试...")
        like_mode()


def like_report(once=True):
    like_num = int(input("点赞数(上限1000)："))

    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    uid = config.get("DedeUserID", 0)
    anchor_id = get_uid(config["room_id"])["data"]["uid"]
    room_id = config.get("room_id", 0)
    csrf = config.get("bili_jct", "")
    query = bili_api.wbi_sign()

    url = f"https://api.live.bilibili.com/xlive/app-ucenter/v1/like_info_v3/like/likeReportV3"

    params = {
        "click_time": like_num,
        "room_id": room_id,
        "uid": uid,
        "anchor_id": anchor_id,
        "csrf": csrf,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/149.0",
        "Cookie": f'buvid3={config["buvid3"]}; SESSDATA={config["SESSDATA"]}; bili_jct={config["bili_jct"]}',
        "Host": "api.live.bilibili.com",
        "Origin": "https://live.bilibili.com",
        "Referer": f'https://live.bilibili.com/{config["room_id"]}',
    }

    params.update(query)

    if uid == 0 or room_id == 0 or csrf == "":
        logger.error(
            f"参数错误，拒绝请求: uid: {uid} | room_id: {room_id} | csrf: {csrf}"
        )
        time.sleep(3)
        main()

    if like_num > 1000:
        params["click_time"] = 1000
        like_num = 1000
        logger.warning("点赞数上限1000，超过部分将不会计算")

    try:
        if once:
            response = requests.post(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if data["code"] == 0:
                    logger.info("点赞成功")
                    time.sleep(3)
                    main()
                else:
                    logger.error(
                        f"点赞失败：code: {data['code']} | msg: {data['message']}"
                    )
                    time.sleep(3)
                    main()
            else:
                logger.error(f"请求失败，错误码：{response.status_code}")
                time.sleep(3)
                main()
        else:
            i = 0
            count = 0
            while True:
                num = random.randint(50, 100)
                if like_num == 0:
                    break
                elif like_num - num >= 0:
                    params["click_time"] = num
                    like_num -= num
                else:
                    params["click_time"] = like_num
                    num = like_num
                    like_num = 0

                response = requests.post(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data["code"] == 0:
                        i += 1
                        count += num
                        logger.info(
                            f"第 {i} 次点赞成功，点赞数：{params["click_time"]}，总数：{count}"
                        )
                    else:
                        i += 1
                        logger.error(
                            f"第 {i} 次点赞失败：code: {data["code"]} | msg: {data["message"]}"
                        )
                else:
                    i += 1
                    logger.error(
                        f"第 {i} 次请求失败，错误码：{response.status_code}"
                    )

                if like_num != 0:
                    time.sleep(2)

            logger.info(f"点赞完成，点赞次数：{i}，点赞数：{count}")
            time.sleep(3)
            main()

    except Exception as e:
        logger.error(traceback.format_exc())
        time.sleep(3)
        main()


def main():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    os.system("cls")

    print(
        f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃             Bilibili Live Latiao Sender            ┃
┃{frontSpace}{currentVersion} ┃
┠────────────────────────────────────────────────────┨
┃                                                    ┃
┃                A Project of Nya-WSL.               ┃
┃                                                    ┃
┃    Copyright © 2021-2025. All rights reserved.     ┃
┃                                                    ┃
┠────────────────────────────────────────────────────┨
┃                TakahashiHaruki & SHDocter  2026/03 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
账号状态：{"已获取" if config["login"] else "未获取"} 目标房间：{config["room_id"] if config["room_id"] != 0 else "未设置"}
———————————————————————————"""
    )

    print(
        """1.登录B站账号
2.设置房间号
3.赠送辣条(需提前准备银瓜子)
4.循环赠送辣条
5.自动点赞(每天上限1000)
———————————————————————————"""
    )

    while True:
        mode_selector = input("请选择: ")
        if mode_selector == "1":
            mode_selector = "login"
            break
        elif mode_selector == "2":
            mode_selector = "get_roomid"
            break
        elif mode_selector == "3":
            mode_selector = "send_latiao"
            break
        elif mode_selector == "4":
            mode_selector = "send_latiao_loop"
            break
        elif mode_selector == "5":
            mode_selector = "like_report"
            break
        else:
            print("输入有误,请重试...")

    print("———————————————————————————")

    if mode_selector == "login":
        login_bilibili()
    elif mode_selector == "send_latiao":
        manual_send_latiao()
    elif mode_selector == "get_roomid":
        get_roomid()
    elif mode_selector == "send_latiao_loop":
        manual_send_latiao(True)
    elif mode_selector == "like_report":
        like_mode()


main()
