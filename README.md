# Media Display Knob

A physical media controller built with a Raspberry Pi Zero 2W and a rotary encoder. Displays the currently playing media from a Windows PC on a screen attached to the Pi, with real-time track info, album art, progress bar, and playback control via the knob.

## How It Works

```
Windows PC                          Raspberry Pi Zero 2W
┌─────────────────────┐             ┌──────────────────────────┐
│  Server.py          │  TCP/12345  │  Client.py               │
│  APIControl.py ─────┼────────────►│  PiScreen.py  → Display  │
│  (Windows Media API)│             │  PiInterface.py → Knob   │
└─────────────────────┘             └──────────────────────────┘
```

The server reads media info from the Windows Global System Media Transport Controls API (the same API used by the Windows taskbar media controls) and streams it to the Pi over TCP. The Pi renders it on screen and sends knob/button events back to control playback.

## Features

- Album art display with rounded corners
- Scrolling marquee for long title and artist names
- Smooth background color fade derived from album art palette
- Progress bar with live time tracking
- Play/pause, next, previous via rotary encoder
- Idle screen when no media is playing
- Connecting screen on startup
- Auto-reconnect if connection drops

## Hardware

- Raspberry Pi Zero 2W
- Rotary encoder (CLK → GPIO 22, DT → GPIO 27, SW → GPIO 17)
- HDMI display

## Project Structure

| File | Runs on | Purpose |
|---|---|---|
| `Server.py` | Windows | TCP server, sends media data to Pi |
| `APIControl.py` | Windows | Reads media info via Windows Media API |
| `Client.py` | Pi | TCP client, routes data to screen and knob |
| `PiScreen.py` | Pi | pygame display renderer |
| `PiInterface.py` | Pi | Rotary encoder GPIO input |
| `setup_server.bat` | Windows | One-time setup: adds server to startup |
| `setup_client.sh` | Pi | One-time setup: installs systemd service |

## Setup

### Windows (Server)

1. Install dependencies:
    ```
    pip install winsdk vibrant-python
    ```

2. Place a `Default.jpg` in the project folder (used when no album art is available).

3. Run `setup_server.bat` — creates a startup entry and launches the server immediately. The server will start automatically on every login from then on.

### Raspberry Pi (Client)

1. Install dependencies:
    ```bash
    pip install pygame lgpio
    ```

2. Copy the client files to the Pi:
    ```
    Client.py  PiScreen.py  PiInterface.py  setup_client.sh  Default.jpg
    ```

3. Run the setup script:
    ```bash
    chmod +x setup_client.sh
    ./setup_client.sh
    ```

    This creates and enables a systemd service that starts the client automatically after the desktop loads on every boot.

4. Update the server IP in `Client.py` if needed:
    ```python
    reader, writer = await asyncio.open_connection('10.0.0.21', 12345)
    ```

## What Gets Displayed

- **Playing**: Album art, track title (scrolling if long), artist name (scrolling if long), elapsed/total time, progress bar. Background color is derived from the album art.
- **Idle**: Default image centered on screen when no media is playing.
- **Connecting**: Animated "Connecting..." text while waiting for the server.

## Knob Controls

| Action | Result |
|---|---|
| Rotate clockwise | Next track |
| Rotate counter-clockwise | Previous track |
| Press | Play / Pause |
