import asyncio
import json
import base64
from PiInterface import Interface
from PiScreen import Screen

async def read(reader, screen):
    while True:
        line = await asyncio.wait_for(reader.readline(), timeout=5.0)
        if not line:
            raise ConnectionResetError("Server closed connection")
        data = json.loads(line)
        if len(data) == 1 and data[0] == "idle":
            screen.set_idle()
        elif len(data) == 9:
            print(data[0:4], data[5:])
            if str(data[0]).startswith("Spotify"):
                thumbnail_bytes = base64.b64decode(data[4])
            else:
                thumbnail_bytes = open("Default.jpg", "rb").read()
            screen.update(data[1], data[2], data[5], data[6], data[7], thumbnail_bytes, data[8])
        elif len(data) == 3:
            screen.update_time(data[0], data[1], data[2])

async def write(writer, n):
    scroll_task = asyncio.create_task(n.scroll())
    click_task  = asyncio.create_task(n.click())
    try:
        while True:
            done, _ = await asyncio.wait(
                {scroll_task, click_task},
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                msg = json.dumps(task.result()) + "\n"
                writer.write(msg.encode())
                await writer.drain()
                if task is scroll_task:
                    scroll_task = asyncio.create_task(n.scroll())
                else:
                    click_task = asyncio.create_task(n.click())
    finally:
        scroll_task.cancel()
        click_task.cancel()

async def main():
    s = Screen()
    n = Interface()
    try:
        while True:
            writer = None
            try:
                reader, writer = await asyncio.open_connection('10.0.0.21', 12345, limit=4*1024*1024)
                print("Connected")
                await asyncio.gather(read(reader, s), write(writer, n))
            except Exception as e:
                print(f"Connection failed: {e}, retrying in 5s...")
                s.reset()
            finally:
                if writer:
                    try:
                        writer.close()
                        await writer.wait_closed()
                    except Exception:
                        pass
            await asyncio.sleep(5)
    finally:
        n.close()

if __name__ == "__main__":
    asyncio.run(main())
