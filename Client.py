import asyncio
import json
import base64
from ButtonTest import button

async def read(s):
    while(True):
        data = ""
        while(True):
            data += (await s.read(4096)).decode()
            if "\n" in data:
                break
        data = json.loads(data[:data.index("\n")])
        if len(data) == 7:
            print(data[0:4], data[5:])
            with open("Thumbnail.jpg", "wb") as f:
                x = base64.b64decode(data[4])
                f.write(x)
        else:
            print(data)

async def write(s):
    while True:
        try:
            n = button()
            x = await n.button()
            msg = json.dumps(x) + "\n"
            s.write(msg.encode())
            await s.drain()
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