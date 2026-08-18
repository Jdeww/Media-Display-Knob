import time
import os
from collections import deque
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as manager
from winsdk.windows.storage.streams import DataReader, Buffer, InputStreamOptions
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus
from vibrant import Vibrant
from MediaState import MediaState, MediaMessageType
_DIR = os.path.dirname(os.path.abspath(__file__))

class MediaData:
    def __init__(self):
        self._title = None
        self._album_title = None
        self._artist = None
        self._thumbnail = None
        self._background_color = None
        self._curr_session = None
        self._log = deque(maxlen=300)

    def _write_log(self, origin, title, album_title, artist, curr_time, total_time, status):
        self._log.append(f"{origin} | {title} | {album_title} | {artist} | {curr_time} | {total_time} | {status}")
        with open(os.path.join(_DIR, "media_log.txt"), "w") as f:
            f.write("\n".join(self._log))

    async def initialize(self):
        #Initialize a "session", used for looking up data about media being played
        self._session = await manager.request_async()
    
    async def get_thumbnail_bytes(self, thumbnail_ref):
        stream = await thumbnail_ref.open_read_async()
        stream_buffer = Buffer(stream.size)
        await stream.read_async(stream_buffer, stream.size, InputStreamOptions.NONE)
        reader = DataReader.from_buffer(stream_buffer)
        img_bytes = bytearray(stream.size)
        reader.read_bytes(img_bytes)
        return bytes(img_bytes)
    
    def _safe_status(self, session):
        #A session can become invalid (e.g. the app was closed) without ever
        #being removed from self._curr_session, and querying it then raises.
        #Treat that the same as "not playing" instead of letting it propagate.
        try:
            return session.get_playback_info().playback_status
        except Exception:
            return None

    async def GetStatus(self):
        curr_session = self._curr_session
        if curr_session and self._safe_status(curr_session) == PlaybackStatus.PLAYING:
            return True
        return False

    async def GetInfo(self):
        curr_session = None
        if self._curr_session and self._safe_status(self._curr_session) is None:
            #Underlying session is no longer valid; stop tracking it so we fall
            #through to scanning for a new session (e.g. Chrome) below.
            self._curr_session = None

        if self._curr_session == None or self._safe_status(self._curr_session) != PlaybackStatus.PLAYING:
            sessions = self._session.get_sessions()
            for s in sessions:
                if self._safe_status(s) == PlaybackStatus.PLAYING:
                    info = await s.try_get_media_properties_async()
                    if info.title:
                        self._curr_session = s
                        curr_session = s
                        break

            if self._curr_session and self._safe_status(self._curr_session) == PlaybackStatus.PAUSED:
                curr_session = self._curr_session

            if curr_session == None:
                for s in sessions:
                    if self._safe_status(s) == PlaybackStatus.PAUSED:
                        info = await s.try_get_media_properties_async()
                        if info.title:
                            self._curr_session = s
                            curr_session = s
                            break

        else:
            curr_session = self._curr_session

        if curr_session:
            #info keeps important data of media playing (title, album title, artist, thumbnail, etc)
            info = await curr_session.try_get_media_properties_async()
            #time_session keeps time related data of the media playing (How long it is, how much is left)
            time_session = curr_session.get_timeline_properties()
            if time_session:
                curr_time = time_session.position.total_seconds()
                total_time = time_session.end_time.total_seconds()
                last_update = time_session.last_updated_time
                status = curr_session.get_playback_info().playback_status == PlaybackStatus.PLAYING
                #Checks if the media is playing or paused
                if status:
                    now = time.time()
                    last_update_unix = last_update.timestamp()
                    elapsed = now - last_update_unix
                    elapsed = max(0.0, elapsed)
                    curr_time = min(curr_time+ elapsed, total_time)
                    #Since time_session does a periodic update every few seconds, we add more time into 
                    #curr_time in order to get the correct amount of time passed

                #Caching previous information in order to not waste resources
                if info.title != self._title or info.album_artist != self._artist or info.album_title != self._album_title:
                    if info.thumbnail:
                        thumbnail_bytes = await self.get_thumbnail_bytes(info.thumbnail)
                        thumbnail_path = os.path.join(_DIR, "Thumbnail.jpg")
                        with open(thumbnail_path, "wb") as f:
                            f.write(thumbnail_bytes)
                        palette = Vibrant().get_palette(thumbnail_path)
                        dark_muted = palette.dark_muted
                        color = list(dark_muted.rgb) if dark_muted else [0, 0, 0]

                        self._title = info.title
                        self._album_title = info.album_title
                        self._artist = info.album_artist
                        self._background_color = color
                        self._thumbnail = thumbnail_bytes
                        
                        
                        self._write_log(curr_session.source_app_user_model_id, info.title, info.album_title, info.album_artist, round(curr_time, 3), total_time, status)


                        #Used only when debugging, not really much of a use in day to day


                        return (
                            MediaState()
                            .set_type(MediaMessageType.FULL)
                            .set_source(curr_session.source_app_user_model_id)
                            .set_title(info.title)
                            .set_artist(info.album_artist)
                            .set_album(info.album_title)
                            .set_thumbnail(thumbnail_bytes)
                            .set_position(round(curr_time, 3))
                            .set_duration(total_time)
                            .set_playing(status)
                            .set_color(tuple(color))
                        )
                    #Check if the media has a thumbnail and if it does, get the raw bytes of the thumbnail
                    #With the dark muted color for the background
                else:


                    self._write_log(curr_session.source_app_user_model_id, self._title, self._album_title, self._artist, round(curr_time, 3), total_time, status)


                    #Used only when debugging, not really much of a use in day to day


                    return (
                        MediaState()
                        .set_type(MediaMessageType.FULL)
                        .set_source(curr_session.source_app_user_model_id)
                        .set_title(self._title)
                        .set_artist(self._artist)
                        .set_album(self._album_title)
                        .set_thumbnail(self._thumbnail)
                        .set_position(round(curr_time, 3))
                        .set_duration(total_time)
                        .set_playing(status)
                        .set_color(tuple(self._background_color))
                    )

        self._write_log("--", "--", "--", "--", 0.00, 0.00, None)
        return MediaState.make_idle()
    
    async def Change(self, val):
        curr_session = self._curr_session
        if curr_session:
            try:
                if val == 1:
                    await curr_session.try_skip_next_async()
                elif val == 2:
                    await curr_session.try_skip_previous_async()
                else:
                    status = await self.GetStatus()
                    await curr_session.try_toggle_play_pause_async()
                    next = await self.GetStatus()
                    if next == status:
                        if not status:
                            await curr_session.try_pause_async()
                        else:
                            await curr_session.try_toggle_play_pause_async()
            except Exception as e:
                print(f"[Change] Error: {e}")