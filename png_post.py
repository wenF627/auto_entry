import boto3
import base64
import hashlib
import time
import requests
import json

# # S3配置
# s3_client = boto3.client('s3')
# bucket_name = 'my-s3-bucket-name'
# s3_key = 'path/to/my/screenshot.png'
#
# # 下载文件并进行Base64编码
# response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
# file_content = response['Body'].read()
# file_base64 = base64.b64encode(file_content).decode('utf-8')


# 本地文件路径
file_path = r'C:\Users\nicole6927\Desktop\Programs\auto_entry\error_ams_already_done.png'

# 读取本地文件并进行Base64编码
with open(file_path, 'rb') as file:
    file_content = file.read()
    file_base64 = base64.b64encode(file_content).decode('utf-8')
# print(file_base64)
# API相关参数
app_key = "eKYIY&2HTgMb@5Ci"
app_sec_key = "9iq^r15fZJ5jQxsK$7&@7B#5yuM$SlpF"
timestamp = str(int(time.time()))
# print(timestamp)
file = "data:image/png;base64," + file_base64
# 生成签名
sign_string = app_key + file + timestamp + app_sec_key + app_key
# print(sign_string)
sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
sign_16 = sign[8:24]
file_path = "signature_data.txt"
with open(file_path, "w") as file:
    file.write(f"sign_string: {sign_string}\n")
    file.write(f"sign: {sign}\n")
# print(sign)
# 构造请求
url = "http://139.224.207.21:8083/adminapi/s3file/uploadByAppkey"  # 使用测试环境地址
payload = {
    "appKey": app_key,
    "file": file,
    "sign": sign_16,
    "timeStamp": timestamp
}
file_path = "payload_data.txt"
# with open(file_path, "w") as file:
#     json.dump(payload, file, indent=4)
print(payload)
# 发送POST请求
response = requests.post(url, json=payload)

# 处理响应
if response.status_code == 200:
    result = response.json()
    if result.get('status'):
        print("上传成功！文件名称:", result['data']['randomName'])
    else:
        print("上传失败:", result.get('message'))
else:
    print("HTTP错误:", response.status_code)
