import asyncio
import websockets
import json
from websockets.exceptions import ConnectionClosedError

class Fitbit:
    def __init__(self, name, uri):
        self.name = name
        self.uri = uri
        self._wait = True

    async def receive_data(self, websocket):
        """WebSocket에서 데이터를 수신하는 코루틴"""
        print(self.name, ": receive_data")
        async for message in websocket:
            # print(message)
            k = json.loads(message)
            print(k)

    async def connect(self):
        """WebSocket에 연결하는 코루틴"""
        print(self.name, ": connect()")

        async with websockets.connect(self.uri) as websocket:
            # 서버에서 데이터를 수신합니다.
            try:
                await self.receive_data(websocket)
                
            except ConnectionRefusedError as err:
                if self._wait:
                    print("대기...")
                    self._wait = False
                    return
            
            except ConnectionClosedError as e:
                print(e, "\n서버끊김.")


async def main():
    """여러 WebSocket 연결을 시작하는 코루틴"""
    fits = [Fitbit("검은색", 'ws://192.168.0.53:8080'), Fitbit("남색", 'ws://192.168.0.37:8080')]
    tasks = [asyncio.create_task(fit.connect()) for fit in fits]

    await asyncio.gather(*tasks)

# 이벤트 루프를 시작하여 주 코루틴을 실행합니다.
if __name__ == "__main__":
    print("__main__")
    asyncio.run(main())
