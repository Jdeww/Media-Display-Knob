import socket
import asyncio
import time
import json
import base64

async def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((socket.gethostbyname(socket.gethostname()), 12345))
        while(True):
            data = ""
            while(True):
                data += s.recv(4096).decode()
                if "\n" in data:
                    break
            data = json.loads(data[:data.index("\n")])
            print(data[0:4], data[5:])
            with open("Thumbnail.jpg", "wb") as f:
                x = base64.b64decode(data[4])
                f.write(x)

if __name__ == "__main__":
    asyncio.run(main())