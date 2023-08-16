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

"""
병원의 서버 컴퓨터에서 실행 될 프로그램
각 fitbit들로 부터 hr 데이터를 받아, 시계열 데이터 생성 및 저장

    data_directory: hr 데이터 저장 경로
    monitoring_uri: hr-app.py의 url/post-data 형식으로
    data: fitbit 별로 데이터가 담길 dictionary
    data_lock: data의 무결성 문제 방지
"""

data_directory = "/home/ni3/Desktop/hr-data/"
monitoring_uri = "http://localhost:9990/post-data"
data = {}
data_lock = Lock()

class Fitbit:
    """
    num: 라즈베리파이 고유번호
    name: 2 fitbit, 4 라즈베리파이를 하나로 인식하게 하는 변수
    uri: 라즈베리파이 ip 주소

    self._wait, self._pong: 연결이 잠시 끊겼을 시, 처리하기 위한 boolean 변수
    self.pth: 데이터가 저장 될 경로
    """
    def __init__(self, num, name, uri):
        self.num = num
        self.name = name
        self.uri = uri
        self.ip = self.uri.split(":")[1].split(".")[-1]
        self._wait = False
        self._pong = False
        self.pth = os.path.join(data_directory, self.name)

        self._mkdir()
        self.set_default()

    """
    name의 data 를 dictionary 형으로 초기화
    """
    def set_default(self, state='-'):
        data[self.name] = {
            'time': '-', 'hr': state,
            'X': '-', 'Y': '-', 'Z': '-', 'ip': self.ip
            }

    """
    경로가 있는지 확인 후, 없으면 생성
    """
    def _mkdir(self):
        if not os.path.exists(self.pth):
            os.mkdir(self.pth)
                
    """
    라즈베리파이로 부터 받은 정보(message)를 저장하고, monitoring-server로 전달
    message의 구조: {'time' : ~~~, 'hr' : ~~~, 'X' ...}
    """
    async def receive_data(self, message):
        k = json.loads(message)
        time = k['time']
        hr_data = k['hr']
        xyz = f"X: {k['X']}, Y: {k['Y']}, Z: {k['Z']}"

        msg = f"time: {time} / hr: {hr_data} / xyz: {xyz} / ip: {self.ip}"

        filepath = os.path.join(self.pth, get_date_for_filename())  # 환자/날짜.txt
        with open(filepath, 'a') as f:
            f.write(msg + '\n')

        # data에 현재 hr 기입
        with data_lock:
            data[self.name] = {
                'time': time, 'hr': hr_data, 
                'xx': k['X'], 'yy': k['Y'], 'zz': k['Z'], 'ip': self.ip
                }
            send_data() # monitoring_server 로 전달


    """
    서버와 라즈베리파이를 연결하는 메소드
    """
    async def connect(self):
        while True:
            try:
                ## 라즈베리파이에 websocket 요청
                async with websockets.connect(self.uri) as ws:
                    logger(f"{self.name}/{self.ip}: connect\\(\\)")
                    self._wait = False

                    ## websocket 연결이 되면, 무한루프를 돌려 신호 대기
                    while True:
                        ## 2초정도 대기 후, 신호가 없으면 에러
                        try:
                            self._pong = False
                            reply = await asyncio.wait_for(ws.recv(), timeout=2)

                        except (asyncio.TimeoutError, ConnectionClosedError):
                            ## 다시 신호 대기를 시킴
                            try:
                                self.set_default('wait')
                                pong = await ws.ping()
                                await asyncio.wait_for(pong, timeout=2)
                                continue
                            ## 만약에 또 문제가 생기면, 현 loop를 빠져나와 다시 연결 요청
                            except:
                                self.set_default('pong')
                                if not self._pong:
                                    self._pong = True
                                    cf = currentframe()
                                    wrn = f'warning: line {cf.f_lineno}'
                                    logger(wrn)
                                break

                        ## 예상하지 못한 에러
                        except:
                            cf = currentframe()
                            wrn = f'warning: line {cf.f_lineno}'
                            logger(wrn)

                        await self.receive_data(reply)  # 받은 데이터 저장 및 전송

            # websocket 연결에 실패한 경우
            except (ConnectionRefusedError, ConnectionClosedError):
                self.set_default('X')
                if not self._wait:
                    self._wait = True
                    wrn = f'{self.name}/{self.ip}:: 연결 끊김'
                    logger(wrn)

            except:
                self.set_default()
                if not self._wait:
                    self._wait = True
                    cf = currentframe()
                    wrn = f'warning: line {cf.f_lineno}'
                    logger(wrn)

            ## 연결에 실패했을 경우에도 연결이 끊긴 것을 모니터링 서버에 표시하기 위해
            finally:
                send_data()

def str_to_datetime(time_str):
    return datetime.datetime.strptime(time_str, "%H:%M:%S")

def get_datetime():
    return str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def get_seconds(time):
    return time.split(':')[-1]

def get_date_for_filename():
    return str(datetime.datetime.now().date()) + ".txt"

def check_directory():
    if not os.path.exists(data_directory):
        os.mkdir(data_directory)

# monitoring-server 로 현재 data 전송
def send_data():
    global data
    try:
        _data = json.dumps(str(data))
        requests.post(monitoring_uri, data=_data)
    except:
        pass

def logger(msg):
    msg = str(msg)
    time = get_datetime()
    
    os.system('echo ' + time + "::: " + msg)


async def main():
    ## fits 에 라즈베리파이 수 만큼 Fitbit 객체를 넣어주어야 함.
    fits = [Fitbit(0, "001", 'ws://192.168.0.53:8080'), Fitbit(1, "001", 'ws://192.168.0.78:8080')]
    tasks = [asyncio.create_task(fit.connect()) for fit in fits]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    logger("__main__")
    check_directory()
    asyncio.run(main())
