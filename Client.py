import asyncio
import json
import base64
from PiInterface import Interface
from PiScreen import Screen

async def read(x, screen):
    while(True):
        data = ""
        while(True):
            chunk = await asyncio.wait_for(x.read(4096), timeout=5.0)
            if not chunk:
                raise ConnectionResetError("Server closed connection")
            data += chunk.decode()
            if "\n" in data:
                break
        data = json.loads(data[:data.index("\n")])
        if len(data) == 1 and data[0] == "idle":
            screen.set_idle()
        elif len(data) == 9:
            print(data[0:4], data[5:])
            if str(data[0]).startswith("Spotify"):
                thumbnail_bytes = base64.b64decode(data[4])
                with open("Thumbnail.jpg", "wb") as f:
                    f.write(thumbnail_bytes)
            else:
                thumbnail_bytes = open("Default.jpg", "rb").read()
            screen.update(data[1], data[2], data[5], data[6], data[7], thumbnail_bytes, data[8])
        elif len(data) == 3:
            screen.update_time(data[0], data[1], data[2])

async def write(x):
    n = Interface()
    scroll_task = asyncio.create_task(n.scroll())
    click_task = asyncio.create_task(n.click())
    while True:
        try:
            done, _ = await asyncio.wait(
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
    s = Screen()
    while True:
        try:
            reader, writer = await asyncio.open_connection('10.0.0.21', 12345)
            print("Connected")
            await asyncio.gather(
                read(reader, s),
                write(writer)
            )
        except (OSError, ConnectionResetError, ConnectionAbortedError, asyncio.TimeoutError) as e:
            print(f"Connection failed: {e}, retrying in 5s...")
            s.reset()
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())