from flask import Flask, request, render_template
import asyncio
import websockets

app = Flask(__name__)

async def websocket_server(websocket, path):
    print("hello, im websoc")
    async for message in websocket:
        print(f"Received message: {message}")
        await websocket.send(f"Echoing back: {message}")

# 라우트 및 뷰 함수 정의
@app.route('/')
async def index():
    start_server = websockets.serve(websocket_server, "localhost", 8000)
    await asyncio.gather(start_server)
    return render_template('index.html')

if __name__ == '__main__':
    asyncio.run(app.run(port=5050))
