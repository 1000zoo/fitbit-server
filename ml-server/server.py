## 딥러닝용 서버


import asyncio
import websockets
import json
from websockets.exceptions import ConnectionClosedError
import os
import datetime
from concurrent.futures import TimeoutError as ConnectionTimeoutError

data_directory = "./hr-data/"
data = {}

class Fitbit:
    def __init__(self, num, name, uri):
        self.num = num
        self.name = name
        self.uri = uri
        self._wait = False
        self._pong = False
        self.pth = os.path.join(data_directory, self.name)
        self.prev_time = None
        data[self.num] = {'name' : self.name, 'hr' : '-'}
        self.mkdir()

    def mkdir(self):
        if not os.path.exists(self.pth):
            os.mkdir(self.pth)
                
    async def receive_data(self, message):
        """WebSocket에서 데이터를 수신하는 코루틴"""
        print(self.name, ": receive_data")

        k = json.loads(message)
        time = k['time']
        hr_data = k['hr']
        xyz = f"X: {k['X']}, Y: {k['Y']}, Z: {k['Z']}"

        print(f"{self.name}: hr->{hr_data}, {xyz}")
        data[self.num] = {'name' : self.name, 'hr' : hr_data}

        # message의 구조:
        # {'time' : ~~~, 'hr' : ~~~, 'X' ...}

        filepath = os.path.join(self.pth, get_date_for_filename())

        if self.prev_time is None:
            self.prev_time = str_to_datetime(time)

        curr_time = str_to_datetime(time)
        time_diff = (curr_time - self.prev_time).total_seconds()

        # if time_diff > 1:
        #     missing_times = int(time_diff) - 1
        #     for i in range(missing_times):
        #         missing_time = self.prev_time + datetime.timedelta(seconds=i+1)
        #         with open(filepath, 'a') as f:
        #             f.write(missing_time.strftime("%H:%M:%S") + ", None" + ", " + str(self.uri) + "\n")

        # elif time_diff == 0:
        #     return

        ip_num = self.uri.split(":")[1].split(".")[-1]
        msg = f"{time} / {hr_data} / {ip_num}"

        with open(filepath, 'a') as f:
            f.write(msg + '\n')

        self.prev_time = str_to_datetime(time)


    async def connect(self):
        """WebSocket에 연결하는 코루틴"""
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
                                pong = await ws.ping()
                                await asyncio.wait_for(pong, timeout=2)
                                continue
                            except:
                                if not self._pong:
                                    self._pong = True
                                    print("...")
                                break
                        
                        await self.receive_data(reply)

            except (ConnectionRefusedError, ConnectionClosedError):
                if not self._wait:
                    self._wait = True
                    print(f"{self.name}: 연결 끊김")

def str_to_datetime(time_str):
    return datetime.datetime.strptime(time_str, "%H:%M:%S")

def get_seconds(time):
    return time.split(':')[-1]

def get_date_for_filename():
    return str(datetime.datetime.now().date()) + ".txt"

def check_directory():
    if not os.path.exists(data_directory):
        os.mkdir(data_directory)

async def handler(websocket, path):
    await websocket.send(str(data))


async def get_server():
    async with websockets.serve(handler, "localhost", 4848):
        await asyncio.Future()

async def main():
    """여러 WebSocket 연결을 시작하는 코루틴"""
    fits = [Fitbit(0, "001", 'ws://192.168.0.83:8080'), Fitbit(1, "001", 'ws://192.168.0.53:8080')]
    tasks = [asyncio.create_task(fit.connect()) for fit in fits]

    await get_server()
    await asyncio.gather(*tasks)

# 이벤트 루프를 시작하여 주 코루틴을 실행.
if __name__ == "__main__":
    print("__main__")
    check_directory()
    asyncio.run(main())
