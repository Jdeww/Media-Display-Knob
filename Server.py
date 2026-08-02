import asyncio
from APIControl import MediaData
import json

async def SendData(s, x):
    m = [0,0,0,0,0,0,0,0,0]
    last_send = 0
    errors = 0
    while True:
        getinfo_task = None
        try:
            getinfo_task = asyncio.ensure_future(x.GetInfo())
            data = await asyncio.wait_for(asyncio.shield(getinfo_task), timeout=4.0)
        except asyncio.CancelledError:
            if getinfo_task and not getinfo_task.done():
                getinfo_task.cancel()
                await asyncio.gather(getinfo_task, return_exceptions=True)
            raise
        except Exception as e:
            if getinfo_task and not getinfo_task.done():
                getinfo_task.cancel()
                await asyncio.gather(getinfo_task, return_exceptions=True)
            task = asyncio.current_task()
            if task and task.cancelling():
                raise asyncio.CancelledError() from e
            print(f"[GetInfo] Error: {e}")
            errors += 1
            if errors >= 3:
                try:
                    await x.initialize()
                    errors = 0
                except Exception:
                    pass
            now = asyncio.get_running_loop().time()
            if now - last_send >= 3.0:
                try:
                    s.write((json.dumps(["idle"]) + "\n").encode())
                    await s.drain()
                    last_send = now
                except Exception:
                    pass
            await asyncio.sleep(min(0.5 * errors, 5.0))
            continue
        errors = 0
        now = asyncio.get_running_loop().time()
        if data[0] == "nothing":
            s.write((json.dumps(["idle"]) + "\n").encode())
            await s.drain()
            m = data
            last_send = now
            await asyncio.sleep(0.8)
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
        await asyncio.sleep(0.2)

async def ReceiveData(s, x):
    while True:
        data = ""
        while True:
            chunk = await s.read(1024)
            if not chunk:
                raise ConnectionResetError("Client disconnected")
            data += chunk.decode()
            if len(data) > 4096:
                raise ValueError("Receive buffer overflow")
            if "\n" in data:
                break
        try:
            data = json.loads(data[:data.index("\n")])
        except json.JSONDecodeError:
            continue
        await x.Change(data)

async def handleClient(reader, writer):
    addr = writer.get_extra_info('peername')
    x = MediaData()
    for attempt in range(5):
        try:
            await x.initialize()
            break
        except Exception as e:
            if attempt == 4:
                print(f"Failed to initialize session for {addr}: {e}")
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass
                return
            await asyncio.sleep(1.0)
    print(f"Connected by {addr}")
    send_task = asyncio.create_task(SendData(writer, x))
    recv_task = asyncio.create_task(ReceiveData(reader, x))
    try:
        done, _ = await asyncio.wait({send_task, recv_task}, return_when=asyncio.FIRST_EXCEPTION)
        for t in done:
            if not t.cancelled() and t.exception():
                print(f"Client Disconnected: {t.exception()}")
    except Exception as e:
        print(f"Client Disconnected: {e}")
    finally:
        send_task.cancel()
        recv_task.cancel()
        await asyncio.gather(send_task, recv_task, return_exceptions=True)
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

async def main():
    loop = asyncio.get_running_loop()
    def _exception_handler(loop, context):
        msg = context.get('message', '')
        if 'Future.set_exception' in msg or 'Future.set_result' in msg:
            return
        loop.default_exception_handler(context)
    loop.set_exception_handler(_exception_handler)

    server = await asyncio.start_server(handleClient, '0.0.0.0', 12345)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
