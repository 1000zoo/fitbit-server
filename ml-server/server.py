## 딥러닝용 서버


import asyncio
import websockets
import json
from websockets.exceptions import ConnectionClosedError
import os
import datetime
from concurrent.futures import TimeoutError as ConnectionTimeoutError
from inspect import currentframe
import requests
from threading import Lock

data_directory = "./hr-data/"
monitoring_uri = "http://localhost:9990/post-data"
data = {}
data_lock = Lock()

class Fitbit:
    def __init__(self, num, name, uri):
        self.num = num
        self.name = name
        self.uri = uri
        self.ip = self.uri.split(":")[1].split(".")[-1]
        self._wait = False
        self._pong = False
        self.pth = os.path.join(data_directory, self.name)
        self.prev_time = None
        self._mkdir()
        self.set_default()

    def set_default(self, state='-'):
        data[self.name] = {'time': '-', 'hr': state, 'ip': self.ip}

    def _mkdir(self):
        if not os.path.exists(self.pth):
            os.mkdir(self.pth)
                
    """
    # message의 구조:
    # {'time' : ~~~, 'hr' : ~~~, 'X' ...}
    """
    async def receive_data(self, message):
        print(self.name, ": receive_data")

        k = json.loads(message)
        time = k['time']
        hr_data = k['hr']
        xyz = f"X: {k['X']}, Y: {k['Y']}, Z: {k['Z']}"

        if self.prev_time is None:
            self.prev_time = str_to_datetime(time)

        msg = f"time: {time} / hr: {hr_data} / ip: {self.ip}"
        print(msg)

        filepath = os.path.join(self.pth, get_date_for_filename())
        with open(filepath, 'a') as f:
            f.write(msg + '\n')

        with data_lock:
            data[self.name] = {'time': time, 'hr': hr_data, 'ip': self.ip}
            send_data()

        self.prev_time = str_to_datetime(time)


    async def connect(self):
        print(self.name, ": connect()")
        
        while True:
            try:
                async with websockets.connect(self.uri) as ws:
                    self._wait = False
                    while True:
                        try:
                            self._pong = False
                            reply = await asyncio.wait_for(ws.recv(), timeout=2)

                        except (asyncio.TimeoutError, ConnectionClosedError):
                            try:
                                self.set_default('wait')
                                pong = await ws.ping()
                                await asyncio.wait_for(pong, timeout=2)
                                continue
                            except:
                                self.set_default('pong')
                                if not self._pong:
                                    self._pong = True
                                    print(f"line {cf.f_lineno}")
                                break

                        except:
                            cf = currentframe()
                            print(f"line {cf.f_lineno}")
                        
                        await self.receive_data(reply)

            except (ConnectionRefusedError, ConnectionClosedError):
                self.set_default('X')
                if not self._wait:
                    self._wait = True
                    print(f"{self.name}: 연결 끊김")

            except OSError as oserror:
                self.set_default()
                if not self._wait:
                    self._wait = True
                    cf = currentframe()
                    print(f"line {cf.f_lineno}")
                    print(oserror)

            except:
                self.set_default()
                if not self._wait:
                    self._wait = True
                    cf = currentframe()
                    print(f"line {cf.f_lineno}")

            finally:
                send_data()

def str_to_datetime(time_str):
    return datetime.datetime.strptime(time_str, "%H:%M:%S")

def get_seconds(time):
    return time.split(':')[-1]

def get_date_for_filename():
    return str(datetime.datetime.now().date()) + ".txt"

def check_directory():
    if not os.path.exists(data_directory):
        os.mkdir(data_directory)

def send_data(): ## request 로 수정
    global data
    try:
        _data = json.dumps(str(data))
        requests.post(monitoring_uri, data=_data)
    except:
        pass


async def main():
    """여러 WebSocket 연결을 시작하는 코루틴"""
    fits = [Fitbit(0, "001", 'ws://192.168.0.53:8080'), Fitbit(1, "001", 'ws://192.168.0.78:8080')]
    tasks = [asyncio.create_task(fit.connect()) for fit in fits]

    await asyncio.gather(*tasks)

# 이벤트 루프를 시작하여 주 코루틴을 실행.
if __name__ == "__main__":
    print("__main__")
    check_directory()
    asyncio.run(main())
