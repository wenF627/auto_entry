from flask import Flask, jsonify, request, send_file

app = Flask(__name__)

# 模拟获取Excel文件和文件名的API
@app.route('/api/get_excel', methods=['GET'])
def get_excel():
    response_data = {
        "excel_url": "http://localhost:5000/download_excel",
        "filename": "testfile.xlsx"
    }
    return jsonify(response_data)

# 模拟Excel文件下载
@app.route('/download_excel', methods=['GET'])
def download_excel():
    return send_file("testfile.xlsx", as_attachment=True)

# 模拟返回结果的API
@app.route('/api/return_results', methods=['POST'])
def return_results():
    data = request.json
    print("Received result:", data)
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(debug=True)
