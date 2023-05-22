import asyncio
import websockets
import json
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['GET'])
def update():
    data = get_data()
    print(data)
    return jsonify({
        'data': data,
    })

def get_data():
    return asyncio.run(socket())

async def socket():
    async with websockets.connect("ws://localhost:4848") as websocket:
        data = await websocket.recv()
        
        return eval(data)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9990)
    # asyncio.run(socket())
