import time
from machine import Pin, time_pulse_us

# modified from https://github.com/Open-STEM/XRP_MicroPython/blob/bc544d66d17d5f135607dbf14dd6737401533085/XRPLib/rangefinder.py

class UltrasoundRange:

    def __init__(self, trigger_pin:int=20, echo_pin:int=21, timeout_us:int=500*2*30):
        """
        A basic class for using the HC-SR04 Ultrasonic Rangefinder.
        The sensor range is between 2cm and 4m.
        Timeouts will return a MAX_VALUE (65535) instead of raising an exception.

        :param trigger_pin: The number of the pin on the microcontroller that's connected to the ``Trig`` pin on the HC-SR04.
        :type trigger_pin: int
        :param echo_pin: The number of the pin on the microcontroller that's connected to the ``Echo`` pin on the HC-SR04.
        :type echo_pin: int
        :param timeout_us: Max microseconds seconds to wait for a response from the sensor before assuming it isn't going to answer. By default set to 30,000 us (0.03 s)
        :type timeout_us: int
        """
        self.timeout_us = timeout_us
        # Init trigger pin (out)
        self._trigger = Pin(trigger_pin, mode=Pin.OUT, pull=None)
        self._trigger.value(0)
        self.MAX_VALUE = 65535

        # Init echo pin (in)
        self.echo = Pin(echo_pin, mode=Pin.IN, pull=None)

        self.mm_dist = 0
        self.last_echo_time = 0
        self.cache_time_us = 3000

    def _send_pulse_and_wait(self):
        """
        Send the pulse to trigger and listen on echo pin.
        We use the method `machine.time_pulse_us()` to get the microseconds until the echo is received.
        """
        self._trigger.value(0) # Stabilize the sensor
        time.sleep_us(5)
        self._trigger.value(1)
        # Send a 10us pulse.
        time.sleep_us(10)
        self._trigger.value(0)
        try:
            pulse_time = time_pulse_us(self.echo, 1, self.timeout_us)
            return pulse_time
        except OSError as exception:
            raise exception

    def distance(self) -> float:
        """
        Get the distance in centimeters by measuring the echo pulse time
        """
        if time.ticks_diff(time.ticks_us(), self.last_echo_time) < self.cache_time_us and not (self.mm_dist == 65535 or self.mm_dist == 0):
            return self.mm_dist

        try:
            pulse_time = self._send_pulse_and_wait()
            if pulse_time <= 0:
                return -1
        except OSError as exception:
            # We don't want programs to crash if the HC-SR04 doesn't see anything in range
            # So we catch those errors and return None instead
            if exception.args[0] == 110: # 110 = ETIMEDOUT
                return -1
            raise exception

        # To calculate the distance we get the pulse_time and divide it by 2
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.034320 cm/us that is 1cm each 29.1us
        self.mm_dist =  10.0*(pulse_time / 2)/29.1
        self.last_echo_time = time.ticks_us()
        return self.mm_dist