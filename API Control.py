import asyncio
import time
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as manager
from winsdk.windows.storage.streams import DataReader, Buffer, InputStreamOptions

async def get_info():
    session = await manager.request_async()
    curr_session = session.get_current_session()

    if curr_session:
        info = await curr_session.try_get_media_properties_async()
        time_session = curr_session.get_timeline_properties()
        if time:
            curr_time = time_session.position.total_seconds()
            total_time = time_session.end_time.total_seconds()
            last_update = time_session.last_updated_time

            now = time.time()

            last_update_unix = last_update.timestamp()
            elapsed = now - last_update_unix
            curr_time += elapsed

            thumbnail_bytes = await get_thumbnail_bytes(info.thumbnail)
            return[
                info.title,
                info.album_artist,
                info.album_title,
                thumbnail_bytes,
                round(curr_time, 3),
                total_time
            ]
        return "No timeline found"
    return "No session found"

async def get_thumbnail_bytes(thumbnail_ref):
    stream = await thumbnail_ref.open_read_async()
    stream_buffer = Buffer(stream.size)
    await stream.read_async(stream_buffer, stream.size, InputStreamOptions.NONE)
    reader = DataReader.from_buffer(stream_buffer)
    img_bytes = bytearray(stream.size)
    reader.read_bytes(img_bytes)
    return bytes(img_bytes)


if __name__ == '__main__':
    yes = True
    while True:
        x = asyncio.run( get_info())
        print(x[0:2] , x[4:])
        if yes:
            with open("Thumbnail.jpg", "wb") as f:
                f.write(x[3])
        time.sleep(1)