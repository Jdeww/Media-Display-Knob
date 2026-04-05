import RPi.GPIO as GPIO
import asyncio

class Interface:
    def __init__(self):
        self.CLK = 22
        self.DT = 27
        self.SW = 17

        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    async def scroll(self):
        try:
            prev_clk = GPIO.input(self.CLK)
            while True:
                clk = GPIO.input(self.CLK)
                dt = GPIO.input(self.DT)

                if clk != prev_clk and clk == GPIO.LOW:  # detected falling edge
                    if dt == GPIO.HIGH:
                        return 1   # clockwise
                    else:
                        return 2   # counter-clockwise

                prev_clk = clk
                await asyncio.sleep(0.0005)

        except KeyboardInterrupt:
            GPIO.cleanup()

    async def click(self):
        try:
            prev_clk = GPIO.input(self.SW)
            while True:
                clk = GPIO.input(self.SW)

                if clk != prev_clk and clk == GPIO.LOW:
                    return 3
                prev_clk = clk
                await asyncio.sleep(0.0005)
        except KeyboardInterrupt:
            GPIO.cleanup()
