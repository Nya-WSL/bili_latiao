import base64

def to_base64(file_path):
    with open(file_path, 'rb') as ico_file:
        # 读取二进制数据
        ico_data = ico_file.read()

        # 转换为Base64
        base64_data = base64.b64encode(ico_data)

        return base64_data

if __name__ == "__main__":
    with open("icon.py", "w", encoding="utf-8") as f:
        f.write(f'logo_base64 = {to_base64("logo.png")}')