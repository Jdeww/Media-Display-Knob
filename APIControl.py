import time
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as manager
from winsdk.windows.storage.streams import DataReader, Buffer, InputStreamOptions
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionPlaybackControls as Controls
import base64

class MediaData:
    def __init__(self):
        pass

    async def get_thumbnail_bytes(self, thumbnail_ref):
        stream = await thumbnail_ref.open_read_async()
        stream_buffer = Buffer(stream.size)
        await stream.read_async(stream_buffer, stream.size, InputStreamOptions.NONE)
        reader = DataReader.from_buffer(stream_buffer)
        img_bytes = bytearray(stream.size)
        reader.read_bytes(img_bytes)
        return bytes(img_bytes)
    
    async def GetStatus(self):
        if await manager.request_async().get_current_session().playback_status == PlaybackStatus.PLAYING:
            return True
        return False

    async def GetInfo(self):
        session = await manager.request_async()
        curr_session = session.get_current_session()

        if curr_session:
            info = await curr_session.try_get_media_properties_async()
            time_session = curr_session.get_timeline_properties()
            if time:
                curr_time = time_session.position.total_seconds()
                total_time = time_session.end_time.total_seconds()
                last_update = time_session.last_updated_time
                if curr_session.get_playback_info().playback_status == PlaybackStatus.PLAYING:
                    now = time.time()

                    last_update_unix = last_update.timestamp()
                    elapsed = now - last_update_unix
                    curr_time += elapsed

                thumbnail_bytes = await self.get_thumbnail_bytes(info.thumbnail)
                status = await self.GetStatus()
                return[
                    curr_session.source_app_user_model_id,
                    info.title,
                    info.album_artist,
                    info.album_title,
                    base64.b64encode(thumbnail_bytes).decode(),
                    round(curr_time, 3),
                    total_time,
                    status
                ]
        return [
            "nothing",
            "--",
            "--",
            "--",
            base64.b64encode(open("Default.jpg", "rb").read()).decode(),
            0.00,
            0.00,
            None
        ]
    
    async def Change(self, val):
        if val == "1":
            Controls.TryChangeChannelUpAsync()
        elif val == "2":
            Controls.TryChangeChannelDownAsync()
        else:
            pause = await self.GetStatus()
            if pause == False:
                Controls.TryPauseAsync()
            else:
                Controls.TryPlayAsync()
        return