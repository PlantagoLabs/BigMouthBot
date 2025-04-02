from machine import I2C, Pin
import asyncio

from vl53l5cx.mp import VL53L5CXMP

from vl53l5cx import DATA_TARGET_STATUS, DATA_DISTANCE_MM
from vl53l5cx import STATUS_VALID, RESOLUTION_8X8

from BMBLib import synapse

class RangeArrayDriver:

    def __init__(self, i2c):
        self.tof = VL53L5CXMP(i2c, lpn=None)
        self.tof.reset()

        if not self.tof.is_alive():
            raise ValueError("VL53L5CX not detected")

        self.tof.init()
        self.tof.resolution = RESOLUTION_8X8

        self.sampling_freq = 2

        self.tof.ranging_freq = self.sampling_freq

        self.tof.start_ranging({DATA_DISTANCE_MM, DATA_TARGET_STATUS})

        self.sampler_task = asyncio.create_task(self._sample_sensor_task())


    async def _sample_sensor_task(self):
        while 1:
            if self.tof.check_data_ready():
                results = self.tof.get_ranging_data()
                distance = results.distance_mm
                status = results.target_status

                distance = self._reorder_8x8_array(distance)
                status = self._reorder_8x8_array(status)

                for i, stat in enumerate(status):
                    if stat != STATUS_VALID:
                        distance[i] = None

                distance_array = []
                for k in range(8):
                    line = distance[k*8:k*8+8]
                    distance_array.append(line)

                synapse.publish('front_range_sensor', distance_array, 'front_range_sensor')

                await asyncio.sleep_ms(int(1000./self.sampling_freq) - 100)
            await asyncio.sleep_ms(50)

    def _reorder_8x8_array(self, distances):
        new_array = []
        for k in range(8):
            for n in range(4):
                new_array.append(distances[2*n + 1 + 56 - 8*k])
                new_array.append(distances[2*n + 56 - 8*k])

        return new_array


