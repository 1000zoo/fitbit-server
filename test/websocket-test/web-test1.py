import asyncio
import websockets
import json
from websockets.exceptions import ConnectionClosedError
import os
from datetime import datetime

class Fitbit:
    def __init__(self, name, uri):
        self.name = name
        self.uri = uri
        self._wait = True

    async def receive_data(self, websocket):
        """Coroutine that will be used to receive data from the WebSocket"""
        print("receive_data method")
        async for message in websocket:
            print(self.name, end=":")
            print(type(message))
            self.save_txt(message)
            
            # data = json.loads(message)
            # Do something with the received data
            # print(self.name, ":", data)
            return

    async def connect(self):
        print(self.name)
        try:
            async with websockets.connect(self.uri) as websocket:
                # Receive data from the server
                await self.receive_data(websocket)
        except ConnectionRefusedError as err:
            if self._wait:
                print("대기...")
                self._wait = False
                return
        
        except ConnectionClosedError as e:
            print(e, "\n서버끊김.")

    def check_dir(self):
        if not self.name in os.listdir():
            os.mkdir(self.name)

    def save_txt(self, data):
        self.check_dir()
        date = datetime.today().strftime('%Y_%m_%d')

        filename = os.path.join(self.name, date + ".txt")
        with open(filename, 'wb') as f: 
            f.write(data)


def main(agents):
    print("main method")
    while True:
        for agent in agents:
            asyncio.get_event_loop().run_until_complete(agent.connect())


if __name__ == '__main__':
    fit1 = Fitbit("검은색", 'ws://192.168.0.53:8080')
    fit2 = Fitbit("남색", 'ws://192.168.0.37:8080')

    agents = [fit1, fit2]
    main(agents)