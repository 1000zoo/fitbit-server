## 모니터링용 서버

from flask import Flask, render_template, jsonify, request, Response
import asyncio
import websockets
import json
from websockets.exceptions import ConnectionClosedError

app = Flask(__name__)
data = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['GET'])
def update():
    try:
        return jsonify({
            'data': data,
        })
    except OSError as e:
        print(e)
        return jsonify({
            'data': data,
        })

@app.route("/post-data", methods=["POST"])
def post_data():
    global data
    _data = eval(json.loads(request.data))
    data = _data
    
    return Response("hello", status=200)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9990, debug=True)
    