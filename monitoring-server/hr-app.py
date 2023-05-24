## 모니터링용 서버

from flask import Flask, render_template, jsonify
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
        get_data()
        return jsonify({
            'data': data,
        })
    except OSError as e:
        print(e)
        return jsonify({
            'data': data,
        })

def get_data():
    asyncio.run(socket())

class Fitbit:
    def __init__(self, num, name, uri):
        self.num = num
        self.name = name
        self.uri = uri
        self._wait = True
        self._pong = True
        data[self.num] = {'name' : self.name, "hr" : '-'}

    async def receive_data(self, websocket):
        """WebSocket에서 데이터를 수신하는 코루틴"""
        print(self.name, ": revceive_data()")
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
            k = json.loads(message)
            data[self.num] = {'name' : self.name, 'hr' : k['hr']}
            return k
        
        except asyncio.TimeoutError:
            print(self.name, ': receive_data timed out')
            data[self.num] = {'name' : self.name, 'hr' : '-'}
            return None
        
        except ConnectionRefusedError:
            data[self.num] = {'name' : self.name, 'hr' : '-'}
            return None
        
    async def connect(self):
        """WebSocket에 연결하는 코루틴"""
        try:
            async with websockets.connect(self.uri) as ws:
                self._wait = False
                while True:
                    try:
                        self._pong = False
                        reply = await asyncio.wait_for(ws.recv(), timeout=1)
                        k = json.loads(reply)
                        data[self.num] = {'name' : self.name, 'hr' : k['hr']}
                        return k
                        
                    except (asyncio.TimeoutError, ConnectionClosedError) as e:
                        data[self.num] = {'name' : self.name, 'hr' : '-'}
                        print(f"{self.name}: {e}")
                        try:
                            pong = await ws.ping()
                            await asyncio.wait_for(pong, timeout=1)
                            continue

                        except:
                            if not self._pong:
                                self._pong = True
                            break
        
        except (ConnectionRefusedError, ConnectionClosedError) as e:
            print(f"{self.name}: {e}")
            data[self.num] = {'name' : self.name, 'hr' : '-'}
            if not self._wait:
                self._wait = True
                print(f"{self.name}: 연결 끊김")

        except:
            data[self.num] = {'name' : self.name, 'hr' : '-'}


fits = [Fitbit(0, "검은색", 'ws://192.168.0.53:8080'), Fitbit(1, "남색", 'ws://192.168.0.37:8080')]

async def socket():
    """여러 WebSocket 연결을 시작하는 코루틴"""
    tasks = [asyncio.create_task(fit.connect()) for fit in fits]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9990, debug=True)
    