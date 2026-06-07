import pygame
import sys
import threading
import time
import io

def _load_unicode_font(size):
    return pygame.font.Font("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", size)

def _round_image(image, radius):
    size = image.get_size()
    mask = pygame.Surface(size, pygame.SRCALPHA)
    mask.fill((0, 0, 0, 0))
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, *size), border_radius=radius)
    image = image.convert_alpha()
    image.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return image

def _draw_rounded_bar(surface, bg_color, fg_color, x, y, w, h, progress):
    r = h // 2
    pygame.draw.rect(surface, bg_color, (x + r, y, w - 2 * r, h))
    pygame.draw.circle(surface, bg_color, (x + r,     y + r), r)
    pygame.draw.circle(surface, bg_color, (x + w - r, y + r), r)
    fill_w = max(min(int(w * progress), w), 2 * r)
    pygame.draw.rect(surface, fg_color, (x + r, y, fill_w - 2 * r, h))
    pygame.draw.circle(surface, fg_color, (x + r,          y + r), r)
    pygame.draw.circle(surface, fg_color, (x + fill_w - r, y + r), r)
    dot_r = h
    dot_cx = max(x + dot_r, min(x + fill_w, x + w - dot_r))
    pygame.draw.circle(surface, (255, 255, 255), (dot_cx, y + r), dot_r)

class Screen:
    def __init__(self):
        self._lock  = threading.Lock()
        self._data  = None
        self._state = "connecting"  # "connecting" | "idle" | "playing"
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def update(self, title, artist, curr_time, total_time, playing, thumbnail_bytes, color):
        with self._lock:
            self._state = "playing"
            self._data = {
                "title":          title,
                "artist":         artist,
                "curr_time":      curr_time,
                "total_time":     total_time,
                "playing":        playing,
                "thumbnail_bytes": thumbnail_bytes,
                "color":          color,
                "updated_at":     time.monotonic()
            }

    def set_idle(self):
        with self._lock:
            self._state = "idle"
            self._data  = None

    def reset(self):
        with self._lock:
            self._state = "connecting"
            self._data  = None

    def update_time(self, curr_time, total_time, playing):
        with self._lock:
            if self._data is not None:
                self._data["curr_time"]  = curr_time
                self._data["total_time"] = total_time
                self._data["playing"]    = playing
                self._data["updated_at"] = time.monotonic()

    def _format_time(self, seconds):
        seconds = int(seconds)
        return f"{seconds // 60}:{seconds % 60:02d}"

    def _loop(self):
        try:
            pygame.mixer.pre_init(0, 0, 0, 0)
            pygame.init()
            pygame.mixer.quit()
            pygame.mouse.set_visible(False)
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
            width, height = screen.get_size()
        except Exception as e:
            print(f"[Screen] Display init failed: {e}")
            return

        font_title   = _load_unicode_font(75)
        font_artist  = _load_unicode_font(38)
        font_small   = pygame.font.SysFont(None, 28)
        font_waiting = pygame.font.SysFont(None, 48)

        thumb_size = int(height * 0.7)
        thumb_cache           = None
        last_thumbnail_bytes  = None

        try:
            idle_surf = _round_image(
                pygame.transform.smoothscale(pygame.image.load("Default.jpg"), (thumb_size, thumb_size)),
                radius=12
            )
        except Exception:
            idle_surf = None
        idle_x = width  // 2 - thumb_size // 2
        idle_y = height // 2 - thumb_size // 2

        text_x   = width // 2
        center_y = height // 2
        bar_w = width // 2 - 60
        bar_h = 10
        bar_x = text_x + 30
        bar_y = center_y + 80
        thumb_x = width  // 4 - thumb_size // 2
        thumb_y = (height - thumb_size) // 2

        # Marquee state
        title_max_w       = width // 2 - 40
        title_clip        = pygame.Surface((title_max_w, font_title.get_height()), pygame.SRCALPHA)
        scroll_x          = 0.0
        scroll_speed      = 45
        scroll_gap        = 80
        last_title        = None
        title_surf        = None
        title_needs_scroll = False

        artist_max_w        = width // 2 - 40
        artist_clip         = pygame.Surface((artist_max_w, font_artist.get_height()), pygame.SRCALPHA)
        artist_scroll_x     = 0.0
        last_artist         = None
        artist_surf         = None
        artist_needs_scroll = False

        # Cached time string
        last_time_str = None
        time_surf     = None

        # Background color fade state
        bg_current = [0.0, 0.0, 0.0]
        bg_target  = [0.0, 0.0, 0.0]
        fade_speed = 3.0

        # Connecting animation
        dot_count    = 0
        dot_timer    = 0.0
        prev_state   = None
        prev_dots    = -1

        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN or event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            dt = clock.tick(30) / 1000.0

            with self._lock:
                data  = self._data
                state = self._state

            if state == "connecting":
                dot_timer += dt
                if dot_timer >= 0.5:
                    dot_timer = 0.0
                    dot_count = (dot_count + 1) % 4
                if state != prev_state or dot_count != prev_dots:
                    screen.fill((0, 0, 0))
                    label = "Connecting" + "." * dot_count
                    surf  = font_waiting.render(label, True, (180, 180, 180))
                    screen.blit(surf, (width // 2 - surf.get_width() // 2, height // 2 - surf.get_height() // 2))
                    pygame.display.flip()
                    prev_dots = dot_count
                prev_state = state
                continue

            if state == "idle":
                if state != prev_state:
                    screen.fill((0, 0, 0))
                    if idle_surf:
                        screen.blit(idle_surf, (idle_x, idle_y))
                    pygame.display.flip()
                prev_state = state
                continue

            prev_state = state

            try:
                if data["thumbnail_bytes"] is not last_thumbnail_bytes:
                    last_thumbnail_bytes = data["thumbnail_bytes"]
                    thumb_cache = _round_image(
                        pygame.transform.smoothscale(
                            pygame.image.load(io.BytesIO(last_thumbnail_bytes)),
                            (thumb_size, thumb_size)
                        ),
                        radius=12
                    )

                if data["title"] != last_title:
                    last_title = data["title"]
                    title_surf = font_title.render(data["title"], True, (255, 255, 255))
                    title_needs_scroll = title_surf.get_width() > title_max_w
                    scroll_x = 0.0

                if title_needs_scroll:
                    loop_w   = title_surf.get_width() + scroll_gap
                    scroll_x = (scroll_x + scroll_speed * dt) % loop_w

                if data["artist"] != last_artist:
                    last_artist = data["artist"]
                    artist_surf = font_artist.render(data["artist"], True, (232, 232, 232))
                    artist_needs_scroll = artist_surf.get_width() > artist_max_w
                    artist_scroll_x = 0.0

                if artist_needs_scroll:
                    artist_loop_w   = artist_surf.get_width() + scroll_gap
                    artist_scroll_x = (artist_scroll_x + scroll_speed * dt) % artist_loop_w

                elapsed  = time.monotonic() - data["updated_at"]
                curr_time = data["curr_time"] + (elapsed if data["playing"] else 0)
                curr_time = min(curr_time, data["total_time"])

                color = data["color"]
                for i in range(3):
                    bg_target[i] = float(color[i])
                    f = min(fade_speed * dt, 1.0)
                    bg_current[i] = min(max(bg_current[i] + (bg_target[i] - bg_current[i]) * f, 0.0), 255.0)

                screen.fill((int(bg_current[0]), int(bg_current[1]), int(bg_current[2])))
                screen.blit(thumb_cache, (thumb_x, thumb_y))

                title_clip.fill((0, 0, 0, 0))
                if title_needs_scroll:
                    loop_w = title_surf.get_width() + scroll_gap
                    title_clip.blit(title_surf, (-int(scroll_x), 0))
                    title_clip.blit(title_surf, (loop_w - int(scroll_x), 0))
                else:
                    title_clip.blit(title_surf, (0, 0))
                screen.blit(title_clip, (text_x + 20, center_y - 84))

                artist_clip.fill((0, 0, 0, 0))
                if artist_needs_scroll:
                    artist_loop_w = artist_surf.get_width() + scroll_gap
                    artist_clip.blit(artist_surf, (-int(artist_scroll_x), 0))
                    artist_clip.blit(artist_surf, (artist_loop_w - int(artist_scroll_x), 0))
                else:
                    artist_clip.blit(artist_surf, (0, 0))
                screen.blit(artist_clip, (text_x + 25, center_y + 6))

                time_str = f"{self._format_time(curr_time)} / {self._format_time(data['total_time'])}"
                if time_str != last_time_str:
                    last_time_str = time_str
                    time_surf = font_small.render(time_str, True, (150, 150, 150))
                screen.blit(time_surf, (text_x + 30, center_y + 100))

                progress = (curr_time / data["total_time"]) if data["total_time"] > 0 else 0
                _draw_rounded_bar(screen, (60, 60, 60), (255, 255, 255), bar_x, bar_y, bar_w, bar_h, progress)

                pygame.display.flip()
            except Exception as e:
                print(f"[Screen] Error: {e}")
