import lgpio
import asyncio

class Interface:
    def __init__(self):
        self.CLK = 22
        self.DT = 27
        self.SW = 17

        self._chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_input(self._chip, self.CLK, lgpio.SET_PULL_UP)
        lgpio.gpio_claim_input(self._chip, self.DT,  lgpio.SET_PULL_UP)
        lgpio.gpio_claim_input(self._chip, self.SW,  lgpio.SET_PULL_UP)

    def close(self):
        lgpio.gpiochip_close(self._chip)

    async def scroll(self):
        prev_clk = lgpio.gpio_read(self._chip, self.CLK)
        while True:
            clk = lgpio.gpio_read(self._chip, self.CLK)
            dt  = lgpio.gpio_read(self._chip, self.DT)

            if clk != prev_clk and clk == 0:
                return 1 if dt == 1 else 2

            prev_clk = clk
            await asyncio.sleep(0.0005)

    async def click(self):
        prev_sw = lgpio.gpio_read(self._chip, self.SW)
        while True:
            sw = lgpio.gpio_read(self._chip, self.SW)

            if sw != prev_sw and sw == 0:
                return 3

            prev_sw = sw
            await asyncio.sleep(0.0005)
