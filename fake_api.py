from flask import Flask, jsonify, send_file, request
import subprocess

app = Flask(__name__)

# Store result data globally
result_data = None


# 根路径路由，用于处理对 http://localhost:5000/ 的请求
@app.route('/')
def index():
    return "Welcome to the Fake API Server!", 200


# 模拟获取Excel文件和文件名的API
has_run = False


@app.route('/api/get_excel', methods=['GET'])
def get_excel():
    global has_run
    if not has_run:
        has_run = True
        subprocess.Popen(["python", "auto_entry.py"])
    response_data = {
        "excel_url": "http://localhost:5000/download_excel",
        "filename": "Descartes_576-67960325_2024-08-16.xlsx"
    }
    return jsonify(response_data)


# 模拟Excel文件下载
@app.route('/download_excel', methods=['GET'])
def download_excel():
    # 返回本地已有的Excel文件
    return send_file(r"C:\Users\YUNBO WANG KING\Desktop\test_auto_entry\Descartes_576-67960325_2024-08-16.xlsx",
                     as_attachment=True)


# 模拟返回结果的API
@app.route('/api/return_results', methods=['POST', 'GET'])
def return_results():
    global result_data

    if request.method == 'POST':
        result_data = request.json
        print("Received result:", result_data)
        return jsonify({"status": "success"}), 200

    elif request.method == 'GET':
        if result_data:
            return jsonify({"status": "success", "data": result_data}), 200
        else:
            return jsonify({"status": "error", "message": "No result data available"}), 404


if __name__ == '__main__':
    app.run(debug=True)
