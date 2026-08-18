import json
import struct
from enum import IntEnum
from typing import Optional

_COUNT_STRUCT = struct.Struct(">I")  # 4-byte big-endian payload length prefix


class MediaMessageType(IntEnum):
    IDLE = 0
    FULL = 1
    TIME_UPDATE = 2


class MediaState:
    """All information about the current playback session, plus
    (de)serialization to/from a length-prefixed frame suitable for sending
    directly over a socket:

        [4-byte payload length][JSON payload]

    The count prefix lets a reader do "read 4 bytes, then read exactly that
    many more" instead of scanning for a delimiter like the current
    newline-terminated JSON does.
    """

    def __init__(
        self,
        msg_type: MediaMessageType = MediaMessageType.IDLE,
        source: str = "--",
        title: str = "--",
        artist: str = "--",
        album: str = "--",
        thumbnail: bytes = b"",
        position: float = 0.0,
        duration: float = 0.0,
        playing: Optional[bool] = None,
        color: tuple = (0, 0, 0),
    ):
        self._type = msg_type
        self._source = source
        self._title = title
        self._artist = artist
        self._album = album
        self._thumbnail = thumbnail
        self._position = position
        self._duration = duration
        self._playing = playing
        self._color = color

    # --- getters ---
    def get_type(self) -> MediaMessageType:
        return self._type

    def get_source(self) -> str:
        return self._source

    def get_title(self) -> str:
        return self._title

    def get_artist(self) -> str:
        return self._artist

    def get_album(self) -> str:
        return self._album

    def get_thumbnail(self) -> bytes:
        return self._thumbnail

    def get_position(self) -> float:
        return self._position

    def get_duration(self) -> float:
        return self._duration

    def get_playing(self) -> Optional[bool]:
        return self._playing

    def get_color(self) -> tuple:
        return self._color

    # --- setters ---
    def set_type(self, value: MediaMessageType) -> "MediaState":
        self._type = value
        return self

    def set_source(self, value: str) -> "MediaState":
        self._source = value
        return self

    def set_title(self, value: str) -> "MediaState":
        self._title = value
        return self

    def set_artist(self, value: str) -> "MediaState":
        self._artist = value
        return self

    def set_album(self, value: str) -> "MediaState":
        self._album = value
        return self

    def set_thumbnail(self, value: bytes) -> "MediaState":
        self._thumbnail = value
        return self

    def set_position(self, value: float) -> "MediaState":
        self._position = value
        return self

    def set_duration(self, value: float) -> "MediaState":
        self._duration = value
        return self

    def set_playing(self, value: Optional[bool]) -> "MediaState":
        self._playing = value
        return self

    def set_color(self, value: tuple) -> "MediaState":
        self._color = value
        return self

    # --- factories for the three message shapes the protocol uses ---
    @staticmethod
    def make_idle() -> "MediaState":
        return MediaState(msg_type=MediaMessageType.IDLE)

    @staticmethod
    def make_time_update(position: float, duration: float, playing: Optional[bool]) -> "MediaState":
        return MediaState(
            msg_type=MediaMessageType.TIME_UPDATE,
            position=position,
            duration=duration,
            playing=playing,
        )

    # --- serialization ---
    def _to_payload(self) -> dict:
        if self._type == MediaMessageType.IDLE:
            return {"type": int(self._type)}
        if self._type == MediaMessageType.TIME_UPDATE:
            return {
                "type": int(self._type),
                "position": self._position,
                "duration": self._duration,
                "playing": self._playing,
            }
        return {
            "type": int(self._type),
            "source": self._source,
            "title": self._title,
            "artist": self._artist,
            "album": self._album,
            "thumbnail": self._thumbnail.hex(),
            "position": self._position,
            "duration": self._duration,
            "playing": self._playing,
            "color": list(self._color),
        }

    def to_bytes(self) -> bytes:
        """Serialize to the raw JSON payload bytes (unframed). Use write_to()
        to send this over a socket with the length-prefix framing."""
        return json.dumps(self._to_payload()).encode("utf-8")

    @staticmethod
    def from_payload(payload: dict) -> "MediaState":
        msg_type = MediaMessageType(payload["type"])
        if msg_type == MediaMessageType.IDLE:
            return MediaState.make_idle()
        if msg_type == MediaMessageType.TIME_UPDATE:
            return MediaState.make_time_update(
                payload["position"], payload["duration"], payload["playing"]
            )
        return MediaState(
            msg_type=msg_type,
            source=payload["source"],
            title=payload["title"],
            artist=payload["artist"],
            album=payload["album"],
            thumbnail=bytes.fromhex(payload["thumbnail"]),
            position=payload["position"],
            duration=payload["duration"],
            playing=payload["playing"],
            color=tuple(payload["color"]),
        )

    @staticmethod
    def from_bytes(payload: bytes) -> "MediaState":
        return MediaState.from_payload(json.loads(payload.decode("utf-8")))

    # --- socket helpers ---
    @staticmethod
    async def read_from(reader) -> "MediaState":
        """Reads one frame from an asyncio.StreamReader: 4-byte count, then
        exactly that many payload bytes."""
        payload = await read_frame(reader)
        return MediaState.from_bytes(payload)

    async def write_to(self, writer) -> None:
        await write_frame(writer, self.to_bytes())


async def read_frame(reader) -> bytes:
    """Reads one [4-byte count][payload] frame and returns the raw payload.
    Used for both MediaState frames and the plain-int control commands the
    client sends back to the server."""
    header = await reader.readexactly(_COUNT_STRUCT.size)
    (count,) = _COUNT_STRUCT.unpack(header)
    return await reader.readexactly(count)


async def write_frame(writer, payload: bytes) -> None:
    writer.write(_COUNT_STRUCT.pack(len(payload)) + payload)
    await writer.drain()
