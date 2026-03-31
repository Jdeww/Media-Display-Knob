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
        if len(data) == 7:
            print(data[0:4], data[5:])
            with open("Thumbnail.jpg", "wb") as f:
                picture = base64.b64decode(data[4])
                f.write(picture)
        else:
            print(data)

async def write(x,s1, s2):
    while True:
        try:
            n = Interface()
            x = await n.scroll()
            msg = json.dumps(x) + "\n"
            s.write(msg.encode())
            await s.drain()
        except ConnectionResetError:
            print("Server Disconnected")

async def main():
    reader, writer = await asyncio.open_connection('10.0.0.21', 12345)
    s = await Interface()
    await asyncio.gather(
        read(reader),
        write(writer, s.scroll(), s.change())
    )

if __name__ == "__main__":
    asyncio.run(main())