import asyncio
from APIControl import MediaData
import json

async def SendData(s,x):
    m = [0,0,0,0,0,0,0,0,0]
    last_send = 0
    while True:
        try:
            data = await x.GetInfo()
        except Exception as e:
            print(f"[GetInfo] Error: {e}")
            await asyncio.sleep(0.5)
            continue
        now = asyncio.get_event_loop().time()
        if data[0] == "nothing":
            s.write((json.dumps(["idle"]) + "\n").encode())
            await s.drain()
            m = data
            last_send = now
        elif data[1] != m[1]:
            s.write((json.dumps(data) + "\n").encode())
            await s.drain()
            m = data
            last_send = now
        elif data[5:8] != m[5:8] or now - last_send >= 2.0:
            s.write((json.dumps(data[5:8]) + "\n").encode())
            await s.drain()
            m = data
            last_send = now
        print(m[0:4],m[5:])
        await asyncio.sleep(0.2)

async def ReceiveData(s,x):
    while(True):
        data = ""
        while(True):
            data += (await s.read(1024)).decode()
            if "\n" in data:
                break
        data = json.loads(data[:data.index("\n")])
        await x.Change(data)

async def handleClient(reader, writer):
    addr = writer.get_extra_info('peername')
    x = MediaData()
    print(f"Connected by {addr}")
    try:
        await asyncio.gather(
            SendData(writer, x),
            ReceiveData(reader, x))
    except Exception as e:
        print(f"Client Disconnected: {e}")

async def main():
    server = await asyncio.start_server(
        handleClient,
        '0.0.0.0',
        12345
    )
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())