import asyncio
import json
from PiInterface import Interface
from PiScreen import Screen
from MediaState import MediaState, MediaMessageType, write_frame

async def read(reader, screen):
    while True:
        state = await asyncio.wait_for(MediaState.read_from(reader), timeout=5.0)
        if state.get_type() == MediaMessageType.IDLE:
            screen.set_idle()
        elif state.get_type() == MediaMessageType.FULL:
            print(state.get_source(), state.get_title(), state.get_artist())
            if state.get_source().startswith("Spotify"):
                thumbnail_bytes = state.get_thumbnail()
            else:
                thumbnail_bytes = open("Default.jpg", "rb").read()
            screen.update(
                state.get_title(),
                state.get_artist(),
                state.get_position(),
                state.get_duration(),
                state.get_playing(),
                thumbnail_bytes,
                state.get_color(),
            )
        elif state.get_type() == MediaMessageType.TIME_UPDATE:
            screen.update_time(state.get_position(), state.get_duration(), state.get_playing())

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
                await write_frame(writer, json.dumps(task.result()).encode())
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
            read_task = None
            write_task = None
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection('Jdew.local', 12345, limit=4*1024*1024),
                    timeout=5.0,
                )
                print("Connected")
                read_task = asyncio.create_task(read(reader, s))
                write_task = asyncio.create_task(write(writer, n))
                done, _ = await asyncio.wait({read_task, write_task}, return_when=asyncio.FIRST_EXCEPTION)
                for t in done:
                    if not t.cancelled() and t.exception():
                        raise t.exception()
            except Exception as e:
                print(f"Connection failed: {e}, retrying in 5s...")
                s.reset()
            finally:
                if read_task:
                    read_task.cancel()
                if write_task:
                    write_task.cancel()
                if read_task or write_task:
                    await asyncio.gather(read_task, write_task, return_exceptions=True)
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
