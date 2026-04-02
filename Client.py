import asyncio
import json
import base64
from PiInterface import Interface

async def read(x):
    while(True):
        data = ""
        while(True):
            data += (await x.read(4096)).decode()
            if "\n" in data:
                break
        data = json.loads(data[:data.index("\n")])
        if len(data) == 8:
            print(data[0:4], data[5:])
            with open("Thumbnail.jpg", "wb") as f:
                picture = base64.b64decode(data[4])
                f.write(picture)
        else:
            print(data)

async def write(x):
    n = Interface()
    scroll_task = asyncio.create_task(n.scroll())
    click_task = asyncio.create_task(n.click())
    while True:
        try:
            done, pending = await asyncio.wait(
                {scroll_task, click_task},
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in done:
                result = task.result()
                msg = json.dumps(result) + "\n"
                x.write(msg.encode())
                await x.drain()

                if task is scroll_task:
                    scroll_task = asyncio.create_task(n.scroll())
                else:
                    click_task = asyncio.create_task(n.click())
        except ConnectionResetError:
            print("Server Disconnected")

async def main():
    reader, writer = await asyncio.open_connection('10.0.0.21', 12345)
    await asyncio.gather(
        read(reader),
        write(writer)
    )

if __name__ == "__main__":
    asyncio.run(main())