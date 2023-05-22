## 딥러닝용 서버

"""

"""

"""
TODO
- 모니터링용 서버로 데이터를 보내야함
    - 일단 보내기만 하면, 기존의 웹 동작 방식때문에,
      누락된 시간은 '-'로 대체될것으로 보임
- 여기에 실시간으로 딥러닝을 돌릴 코드를 추가해야할지
  아니면 일단 txt로 저장했으니, csv로 바꾸기도 수월할 것이고
  따라서 따로 딥러닝용 파일을 만들것인지
"""

import asyncio
import websockets
import json
from websockets.exceptions import ConnectionClosedError
import os
import datetime

data_directory = "./hr-data/"

class Fitbit:
    def __init__(self, name, uri):
        self.name = name
        self.uri = uri
        self._wait = True
        self.pth = os.path.join(data_directory, self.name)
        self.prev_time = None
        self.mkdir()

    def mkdir(self):
        if not os.path.exists(self.pth):
            os.mkdir(self.pth)

    async def receive_data(self, websocket):
        """WebSocket에서 데이터를 수신하는 코루틴"""
        print(self.name, ": receive_data")
        try:
            async for message in websocket:
                # message의 구조:
                # {'time' : ~~~, 'hr' : ~~~, 'X' ...}
                k = json.loads(message)
                time = k['time']
                hr = k['hr']
                temp_data = {'name' : self.name, 'hr' : hr}
                """
                <-여기에 통신하는 코드 추가하면 될 듯->
                """

                # 저장경로는 디바이스의 이름/날짜.txt
                filepath = os.path.join(self.pth, get_date_for_filename())

                ## 처음 실행할 때 이전 시간 초기화
                if self.prev_time is None:
                    self.prev_time = str_to_datetime(time)
                
                curr_time = str_to_datetime(time)
                time_diff = (curr_time - self.prev_time).total_seconds()
                # 현재시간과 가장 최근에 저장된 시간이 1초 보다 더 차이나면
                # 그 사이시간의 값을 None으로 저장
                if time_diff > 1:
                    missing_times = int(time_diff) - 1
                    for i in range(missing_times):
                        missing_time = self.prev_time + datetime.timedelta(seconds=i+1)
                        with open(filepath, 'a') as f:
                            f.write(missing_time.strftime("%H:%M:%S") + ", None\n")
                
                # 만약 이전의 시간과 현재의 시간이 같다면 (같은 초 단위의 시간이 들어올 때)
                # skip
                elif time_diff == 0:
                    continue

                with open(filepath, 'a') as f:
                    f.write(time + ", " + str(hr) + '\n')

                # 가장 최근 시간을 현재의 시간으로
                self.prev_time = str_to_datetime(time)
                return
        except OSError as err:
            print(err)
            

    async def connect(self):
        """WebSocket에 연결하는 코루틴"""
        print(self.name, ": connect()")

        async with websockets.connect(self.uri) as websocket:
            # 서버에서 데이터를 수신
            try:
                while True:
                    await self.receive_data(websocket)
                
            except ConnectionRefusedError as err:
                if self._wait:
                    print("대기...")
                    self._wait = False
                    return
            
            except ConnectionClosedError as e:
                print(e, "\n서버끊김.")


def str_to_datetime(time_str):
    return datetime.datetime.strptime(time_str, "%H:%M:%S")

def get_seconds(time):
    return time.split(':')[-1]

def get_date_for_filename():
    return str(datetime.datetime.now().date()) + ".txt"

def check_directory():
    if not os.path.exists(data_directory):
        os.mkdir(data_directory)

async def main():
    """여러 WebSocket 연결을 시작하는 코루틴"""
    print("main")
    fits = [Fitbit("검은색", 'ws://192.168.0.53:8080'), Fitbit("남색", 'ws://192.168.0.37:8080')]
    tasks = [asyncio.create_task(fit.connect()) for fit in fits]

    while True:
        try:
            await asyncio.gather(*tasks)
        except ConnectionRefusedError as e:
            print(e)
        except OSError as e:
            print(e)



# 이벤트 루프를 시작하여 주 코루틴을 실행.
if __name__ == "__main__":
    print("__main__")
    check_directory()
    asyncio.run(main())
