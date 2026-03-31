import RPi.GPIO as GPIO
import asyncio

class Interface:
    def __init__(self):
        pass

    async def scroll(self):
        CLK = 22
        DT = 27
        SW = 17

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        try:
            prev_clk = GPIO.input(CLK)
            while True:
                clk = GPIO.input(CLK)
                dt = GPIO.input(DT)

                if clk != prev_clk and clk == GPIO.LOW:  # detected falling edge
                    if dt == GPIO.HIGH:
                        return 1   # clockwise
                    else:
                        return 2   # counter-clockwise

                prev_clk = clk
                await asyncio.sleep(0)

        except KeyboardInterrupt:
            GPIO.cleanup()

    async def click(self):
        SW = 17
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        try:
            prev_clk = GPIO.input(SW)
            while True:
                clk = GPIO.input(SW)

                if clk != prev_clk and clk == GPIO.LOW:
                    return 3
                prev_clk = clk
                await asyncio.sleep(0)
        except KeyboardInterrupt:
            GPIO.cleanup()
