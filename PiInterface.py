import lgpio
import asyncio
import threading
import time

class Interface:
    def __init__(self):
        self._CLK = 22
        self._DT  = 27
        self._SW  = 17

        self._chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_input(self._chip, self._CLK, lgpio.SET_PULL_UP)
        lgpio.gpio_claim_input(self._chip, self._DT,  lgpio.SET_PULL_UP)
        lgpio.gpio_claim_input(self._chip, self._SW,  lgpio.SET_PULL_UP)

        self._scroll_q = asyncio.Queue()
        self._click_q  = asyncio.Queue()
        self._loop     = asyncio.get_event_loop()
        self._stop     = threading.Event()
        threading.Thread(target=self._poll, daemon=True).start()

    def _poll(self):
        prev_clk = lgpio.gpio_read(self._chip, self._CLK)
        prev_sw  = lgpio.gpio_read(self._chip, self._SW)
        while not self._stop.is_set():
            clk = lgpio.gpio_read(self._chip, self._CLK)
            sw  = lgpio.gpio_read(self._chip, self._SW)
            if clk != prev_clk and clk == 0:
                dt = lgpio.gpio_read(self._chip, self._DT)
                self._loop.call_soon_threadsafe(
                    self._scroll_q.put_nowait, 1 if dt == 1 else 2)
            if sw != prev_sw and sw == 0:
                self._loop.call_soon_threadsafe(self._click_q.put_nowait, 3)
            prev_clk = clk
            prev_sw  = sw
            time.sleep(0.005)

    def close(self):
        self._stop.set()
        lgpio.gpiochip_close(self._chip)

    async def scroll(self):
        return await self._scroll_q.get()

    async def click(self):
        return await self._click_q.get()
