from flask import Flask, jsonify, send_file

app = Flask(__name__)

# 根路径路由，用于处理对 http://localhost:5000/ 的请求
@app.route('/')
def index():
    return "Welcome to the Fake API Server!", 200

# 模拟获取Excel文件和文件名的API
@app.route('/api/get_excel', methods=['GET'])
def get_excel():
    response_data = {
        "excel_url": "http://localhost:5000/download_excel",
        "filename": "Descartes_784-08441064_2024-08-16.xlsx"
    }
    return jsonify(response_data)

# 模拟Excel文件下载
@app.route('/download_excel', methods=['GET'])
def download_excel():
    # 返回本地已有的Excel文件
    return send_file(r"C:\Users\nicole6927\Desktop\Descartes_784-08441064_2024-08-16.xlsx", as_attachment=True)  # 替换为您的Excel文件路径

# 模拟返回结果的API
@app.route('/api/return_results', methods=['POST'])
def return_results():
    data = request.json
    print("Received result:", data)
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(debug=True)
