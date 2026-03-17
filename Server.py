import threading
import asyncio
import socket
from API_Control import MediaData
import time
import json

async def SendData():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((socket.gethostbyname(socket.gethostname()), 12345))
        s.listen()
        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    print(f"Connected by {addr}")
                    while True:
                        n = MediaData()
                        x = await n.get_info()
                        conn.sendall((json.dumps(x) + "\n").encode())
                        time.sleep(100)
            except ConnectionResetError:
                print("Client Disconnected")


async def main():
    while True:
        n = MediaData()
        x = await n.get_info()
        print(x[0:4] , x[5:])
        with open("Thumbnail.jpg", "wb") as f:
            f.write(x[4])
        time.sleep(1)


if __name__ == "__main__":
    asyncio.run(SendData())