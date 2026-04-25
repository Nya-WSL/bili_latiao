# coding=utf-8
import log
import random
import bili_api
import traceback
import icon as logo_data
import sys, os, json, requests, time, logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import threading

currentVersion = "2.3.2"
logger = log.logger


# 全局异常处理钩子
def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("未知错误！", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception

# 初始化配置文件
if not os.path.exists("config.json"):
    config = {"uname": "", "room_id": "31842"}
    with open("config.json", "w+", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# 校验配置文件
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

if not config.get("room_id", ""):
    config["room_id"] = "31842"

with open("config.json", "w+", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=4)

class BiliLatiaoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Bilibili Live Latiao Sender")
        self.root.geometry("600x800")
        self.root.resizable(False, False)

        # 设置窗口图标
        try:
            icon_data = logo_data.logo_base64
            # 创建PhotoImage对象
            icon = tk.PhotoImage(data=icon_data)

            # 设置窗口图标
            self.root.iconphoto(True, icon)

            # 保存引用防止被垃圾回收
            self.icon = icon
        except:
            pass

        self.load_config()
        self.setup_ui()
        self.update_status()

        # 重定向日志到GUI
        self.log_handler = GUILogHandler(self.log_text)
        self.log_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s', '%Y-%m-%d %H:%M:%S'))
        logger.addHandler(self.log_handler)

    def load_config(self):
        with open("config.json", "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def save_config(self):
        with open("config.json", "w+", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="哔哩哔哩辣条姬", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 5))

        version_label = ttk.Label(main_frame, text=f"V {currentVersion}", font=("Arial", 9))
        version_label.pack(pady=(0, 10))

        # 状态框架
        status_frame = ttk.LabelFrame(main_frame, text="状态", padding="10")
        status_frame.pack(fill=tk.X, pady=5)

        self.login_status_var = tk.StringVar()
        self.room_status_var = tk.StringVar()

        ttk.Label(status_frame, textvariable=self.login_status_var).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Label(status_frame, textvariable=self.room_status_var).grid(row=1, column=0, sticky=tk.W, padx=5)

        # 操作框架
        action_frame = ttk.LabelFrame(main_frame, text="操作", padding="10")
        action_frame.pack(fill=tk.X, pady=10)

        # 房间号设置
        room_frame = ttk.Frame(action_frame)
        room_frame.pack(fill=tk.X, pady=5)

        # 左侧：标签和输入框
        room_left = ttk.Frame(room_frame)
        room_left.pack(side=tk.LEFT)
        ttk.Label(room_left, text="房间号:").pack(side=tk.LEFT, padx=5)
        self.room_id_var = tk.StringVar()
        self.room_id_var.set(str(self.config.get("room_id", "")))
        ttk.Entry(room_left, textvariable=self.room_id_var, width=15).pack(side=tk.LEFT, padx=5)

        # 右侧：按钮
        room_right = ttk.Frame(room_frame)
        room_right.pack(side=tk.RIGHT)
        ttk.Button(room_right, text="设置房间", command=self.set_roomid).pack(side=tk.LEFT, padx=5)
        self.login_btn = ttk.Button(room_right, text="登录B站账号", command=self.login_bilibili).pack(side=tk.LEFT, padx=5)

        # 辣条赠送
        latiao_frame = ttk.Frame(action_frame)
        latiao_frame.pack(fill=tk.X, pady=5)

        # 左侧：标签和输入框
        latiao_left = ttk.Frame(latiao_frame)
        latiao_left.pack(side=tk.LEFT)
        ttk.Label(latiao_left, text="辣条数:").pack(side=tk.LEFT, padx=5)
        self.latiao_num_var = tk.StringVar()
        self.latiao_num_var.set("1")
        ttk.Entry(latiao_left, textvariable=self.latiao_num_var, width=15).pack(side=tk.LEFT, padx=5)

        # 右侧：按钮
        latiao_right = ttk.Frame(latiao_frame)
        latiao_right.pack(side=tk.RIGHT)
        ttk.Button(latiao_right, text="赠送", command=self.send_latiao).pack(side=tk.LEFT, padx=5)
        ttk.Button(latiao_right, text="循环赠送", command=self.send_latiao_loop).pack(side=tk.LEFT, padx=5)

        # 点赞
        like_frame = ttk.Frame(action_frame)
        like_frame.pack(fill=tk.X, pady=5)

        # 左侧：标签和输入框
        like_left = ttk.Frame(like_frame)
        like_left.pack(side=tk.LEFT)
        ttk.Label(like_left, text="点赞数:").pack(side=tk.LEFT, padx=5)
        self.like_num_var = tk.StringVar()
        self.like_num_var.set("1000")
        ttk.Entry(like_left, textvariable=self.like_num_var, width=15).pack(side=tk.LEFT, padx=5)

        # 右侧：按钮
        like_right = ttk.Frame(like_frame)
        like_right.pack(side=tk.RIGHT)
        ttk.Button(like_right, text="一次点满", command=lambda: self.like_report(True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(like_right, text="手动模拟", command=lambda: self.like_report(False)).pack(side=tk.LEFT, padx=5)

        # 日志显示
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state='disabled', font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 停止按钮
        self.stop_btn = ttk.Button(main_frame, text="停止操作", command=self.stop_operation, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=5)

        # 帮助按钮
        self.help_btn = ttk.Button(main_frame, text="使用说明", command=self.help_operation)
        self.help_btn.pack(fill=tk.X, pady=5)
        self.running = False

    def update_status(self):
        self.login_status_var.set(f"登录用户: {self.config.get('uname', None)}")
        self.room_status_var.set(f"目标房间: {self.config.get('room_id', '未设置')} - {bili_api.get_uname(bili_api.get_uid(self.config.get('room_id', 31842)).get('data', {'uid': 31842}).get('uid', 31842))}")

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()

    def login_bilibili(self):
        self.qr_window = None
        self.loginInfo = None

        def login_thread():
            try:
                self.log("正在获取登录二维码...")
                self.loginInfo = bili_api.get_qrcode()

                # 显示登录对话框
                self.root.after(0, self.show_login_dialog)

            except Exception as e:
                logger.error(f"登录出错: {str(e)}")
                messagebox.showerror("错误", f"登录出错: {str(e)}")

        threading.Thread(target=login_thread, daemon=True).start()

    def show_login_dialog(self):
        self.qr_window = tk.Toplevel(self.root)
        self.qr_window.title("扫码登录")
        self.qr_window.resizable(False, False)
        self.qr_window.transient(self.root)
        self.qr_window.grab_set()

        # 二维码
        img = Image.open("login.png")
        try:
            resize_method = Image.Resampling.LANCZOS  # type: ignore
        except AttributeError:
            resize_method = Image.LANCZOS  # type: ignore
        img = img.resize((250, 250), resize_method)
        photo = ImageTk.PhotoImage(img)

        label = ttk.Label(self.qr_window, image=photo)
        setattr(label, 'image', photo)
        label.pack(pady=20)

        # 提示文字
        ttk.Label(self.qr_window, text="请使用B站APP扫描二维码").pack(pady=(0, 10))

        # 确定按钮
        btn_frame = ttk.Frame(self.qr_window)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="已扫码", width=15, command=self.on_login_confirm).pack()

        self.qr_window.geometry("300x380")

    def on_login_confirm(self):
        # 关闭二维码窗口
        if self.qr_window:
            self.qr_window.destroy()
            self.qr_window = None

        # 执行登录验证
        def check_login():
            try:
                status = bili_api.login(self.loginInfo)
                if status == True:
                    self.load_config()
                    self.update_status()
                else:
                    self.log(f"登录失败: {status}")
            except Exception as e:
                logger.error(f"登录出错: {str(e)}")

        threading.Thread(target=check_login, daemon=True).start()

    def set_roomid(self):
        room_id = self.room_id_var.get().strip()
        if room_id:
            self.config["room_id"] = str(room_id) # 不确定未来是否会超出int范围，以防万一直接使用字符串
            self.save_config()
            self.update_status()
            self.log(f"房间号已设置为: {room_id}")
        else:
            messagebox.showerror("错误", "房间号不能为空")

    def send_latiao(self):
        if not self.check_login_and_room():
            return

        try:
            num = int(self.latiao_num_var.get())
        except ValueError:
            messagebox.showerror("错误", "辣条数量必须是数字")
            return

        def send_thread():
            self.set_running(True)
            try:
                self.send_latiao_impl(num)
            finally:
                self.set_running(False)

        threading.Thread(target=send_thread, daemon=True).start()

    def send_latiao_impl(self, num):
        url = "https://api.live.bilibili.com/gift/v2/gift/send"
        room_info = bili_api.get_uid(self.config["room_id"])
        data = {
            "gift_id": 1,
            "gift_num": num,
            "ruid": room_info["data"]["uid"],
            "coin_type": "silver",
            "biz_id": self.config["room_id"],
            "csrf": self.config["bili_jct"],
            "csrf_token": self.config["bili_jct"],
        }
        headers = {
            "Cookie": f'SESSDATA={self.config["SESSDATA"]}; bili_jct={self.config["bili_jct"]}',
            "Origin": "https//live.bilibili.com",
            "Referer": f'https://live.bilibili.com/{self.config["room_id"]}',
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        }

        response = requests.post(url=url, data=data, headers=headers)
        response.encoding = "utf-8"
        if response.status_code == 200:
            response = response.json()
            if response["code"] == 0:
                msg = f'{response["data"]["uname"]} 在 {room_info["data"]["room_id"]} {response["data"]["gift_action"]} {response["data"]["gift_num"]} 个 {response["data"]["gift_name"]}'
                logger.info(msg)
            else:
                logger.info(response["msg"])
        else:
            logger.error(f"发送辣条失败: {response.status_code}")

    def send_latiao_loop(self):
        if not self.check_login_and_room():
            return

        try:
            num = int(self.latiao_num_var.get())
        except ValueError:
            messagebox.showerror("错误", "辣条数量必须是数字")
            return

        def loop_thread():
            self.set_running(True)
            try:
                count = num
                while count > 0 and self.running:
                    self.send_latiao_impl(1)
                    count -= 1
                    if count > 0 and self.running:
                        time.sleep(2)
                self.log(f"循环赠送完成，共赠送 {num - count} 个辣条")
            finally:
                self.set_running(False)
        
        threading.Thread(target=loop_thread, daemon=True).start()

    def like_report(self, once=True):
        if not self.check_login_and_room():
            return

        try:
            like_num = int(self.like_num_var.get())
        except ValueError:
            messagebox.showerror("错误", "点赞数必须是数字")
            return

        def like_thread():
            self.set_running(True)
            try:
                self.like_report_impl(like_num, once)
            finally:
                self.set_running(False)

        threading.Thread(target=like_thread, daemon=True).start()

    def like_report_impl(self, like_num, once):
        uid = self.config.get("DedeUserID", 0)
        anchor_id = bili_api.get_uid(self.config["room_id"])["data"]["uid"]
        room_id = self.config.get("room_id", 0)
        csrf = self.config.get("bili_jct", "")
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
            "Cookie": f'buvid3={self.config["buvid3"]}; SESSDATA={self.config["SESSDATA"]}; bili_jct={self.config["bili_jct"]}',
            "Host": "api.live.bilibili.com",
            "Origin": "https://live.bilibili.com",
            "Referer": f'https://live.bilibili.com/{self.config["room_id"]}',
        }

        params.update(query)

        if uid == 0 or room_id == 0 or csrf == "":
            logger.error(f"参数错误，拒绝请求: uid: {uid} | room_id: {room_id} | csrf: {csrf}")
            return

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
                    else:
                        logger.error(f"点赞失败：code: {data['code']} | msg: {data['message']}")
                        messagebox.showerror("失败", f"点赞失败：{data['message']}")
                else:
                    logger.error(f"请求失败，错误码：{response.status_code}")
                    messagebox.showerror("失败", f"请求失败，错误码：{response.status_code}")
            else:
                i = 0
                count = 0
                while like_num > 0 and self.running:
                    num = random.randint(50, 100)
                    if like_num - num >= 0:
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
                            msg = f"第 {i} 次点赞成功，点赞数：{params['click_time']}，总数：{count}"
                            logger.info(msg)
                        else:
                            i += 1
                            msg = f"第 {i} 次点赞失败：code: {data['code']} | msg: {data['message']}"
                            logger.error(msg)
                    else:
                        i += 1
                        msg = f"第 {i} 次请求失败，错误码：{response.status_code}"
                        logger.error(msg)

                    if like_num != 0 and self.running:
                        time.sleep(2)
                
                logger.info(f"点赞完成，点赞次数：{i}，点赞数：{count}")

        except Exception as e:
            logger.error(traceback.format_exc())
            messagebox.showerror("错误", f"点赞出错: {str(e)}")

    def check_login_and_room(self):
        if not self.config.get("uname"):
            messagebox.showwarning("警告", "未登录B站账号，请先登录")
            return False

        if not self.config.get("room_id"):
            messagebox.showwarning("警告", "未设置房间号，请先设置")
            return False

        return True

    def set_running(self, running):
        self.running = running
        self.stop_btn.config(state=tk.NORMAL if running else tk.DISABLED)
    
    def stop_operation(self):
        self.running = False
        self.log("正在停止操作...")
    
    def help_operation(self):
        self.log("""⬇功能列表⬇
登录账号：点击按钮会弹出二维码，由于B站流程限制，需扫码并在APP上确认后点击已扫码按钮获取登录状态
设置房间：输入房间号后点击设置房间，会自动查询主播信息
赠送辣条：一次性赠送设置的数量，账号里需要有足够的银瓜子
循环赠送：每2秒赠送1个辣条直到设置的数量，账号里需要有足够的银瓜子
一次点满：一次性点满1000个赞，虽然目前没遇到过，但过于明显，可能会被B站判定无效
手动模拟：模拟手动点赞，每2秒随机点赞50-100个，直到设置的点赞数
停止操作：停止当前循环操作（循环赠送、手动模拟）
⬆功能列表⬆

注：所有功能均需登录B站账号并设置房间号后才能使用
注：B站限制1000赞/每人/每直播间，超过1000属于无效点赞
注：虽然很多已“下架”的礼物B站都没有删除礼物id，但是绝大多数这类礼物都有相应的赠送条件；且由于合规风险，不打算支持赠送电池礼物

使用本软件进行自动化操作（如赠送礼物、点赞等）存在违反BILIBILI平台《用户协议》的风险，可能导致您的B站账号面临限制、封禁或其他平台处罚措施
请您在使用前充分评估并自行承担由此产生的风险
开发者仅提供软件的技术实现，对于因使用本软件导致的B站账号封禁、平台积分/虚拟财产损失，开发者不承担直接的赔偿责任

本软件未获得BILIBILI官方授权，与BILIBILI官方无任何关联
本软件遵循MIT开源许可协议，仅供技术交流与学习，未经书面授权，禁止用于任何商业盈利目的
在使用本软件时，应严格遵守相关法律法规及平台规则，严禁利用本软件从事任何违法违规活动（包括但不限于恶意刷榜、破坏平台公平秩序等）

如认为本软件违反《信息网络传播权保护条例》或《数字千年版权法》，请版权方联系我们（https://github.com/Nya-WSL/bili_latiao）
""")


class GUILogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
    
    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.config(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.config(state='disabled')
        self.text_widget.after(0, append)

def main():
    root = tk.Tk()
    BiliLatiaoGUI(root).help_operation()
    root.mainloop()


if __name__ == "__main__":
    main()