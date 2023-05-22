import asyncio

async def fun1():
    await asyncio.sleep(3)
    print("hello")

async def fun2():
    try:
        await asyncio.wait_for(fun1(), timeout=1)
        print("done")
    except TimeoutError as err:
        print("timeout")

    except:
        print("error")

asyncio.run(fun2())