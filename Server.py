import asyncio
import socket
from API_Control import MediaData
import json

async def SendData(s):
    m = [0,0,0,0,0,0,0]
    while True:
        n = MediaData()
        x = await n.get_info()
        if (x[1] != m[1]):
            s.write((json.dumps(x) + "\n").encode())
            m = x
        else:
            s.write((json.dumps(x[5:]) + "\n").encode())
        await s.drain()
        await asyncio.sleep(1)

async def ReceiveData(s):
    while(True):
        data = ""
        while(True):
            data += (await s.read(1024)).decode()
            if "\n" in data:
                break
        data = json.loads(data[:data.index("\n")])
        print(data)

async def handleClient(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Connected by {addr}")
    try:
        await asyncio.gather(
            SendData(writer),
            ReceiveData(reader))
    except ConnectionResetError:
        print("Client Disconnected")

async def main():
    server = await asyncio.start_server(
        handleClient,
        socket.gethostbyname(socket.gethostname()),
        12345
    )
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())