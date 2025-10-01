from machine import I2C, Pin
import time
import asyncio

from vl53l5cx.mp import VL53L5CXMP

from vl53l5cx import DATA_TARGET_STATUS, DATA_DISTANCE_MM
from vl53l5cx import STATUS_VALID, RESOLUTION_8X8
from vl53l5cx import RANGING_MODE_CONTINUOUS, RANGING_MODE_AUTONOMOUS 

from BMBLib import synapse
from BMBLib import profiler

class RangeArrayDriver:

    def __init__(self, i2c, sampling_freq=10, sharpener_percent=5):
        self.tof = VL53L5CXMP(i2c, lpn=None)
        self.tof.reset()
        if not self.tof.is_alive():
            raise ValueError("VL53L5CX not detected")

        self.tof.init()
        self.tof.resolution = RESOLUTION_8X8

        self.sampling_freq = sampling_freq

        self.tof.ranging_freq = self.sampling_freq
        self.tof.ranging_mode = RANGING_MODE_CONTINUOUS 
        self.tof.sharpener_percent = sharpener_percent

        self.tof.start_ranging({DATA_DISTANCE_MM, DATA_TARGET_STATUS})
        self.sampler_task = asyncio.create_task(self._sample_sensor_task())

    @profiler.profile("range_array.read")
    def _read_sensor(self):
        return self.tof.get_ranging_data()
    
    @profiler.profile("range_array.check")
    def _check_sensor(self):
        return self.tof.check_data_ready()

    async def _sample_sensor_task(self):
        while 1:
            if self._check_sensor():
                t0 = time.ticks_ms()
                results = self._read_sensor()
                distance = results.distance_mm
                status = results.target_status

                for i, stat in enumerate(status):
                    if stat != STATUS_VALID:
                        distance[i] = None

                distance_array = [] #[distance[i:i+8] for i in range(0, 64, 8)]
                for n in [6, 7, 4, 5, 2, 3, 0, 1]:
                    array_line = []
                    array_line.append(distance[n + 56])
                    array_line.append(distance[n + 48])
                    array_line.append(distance[n + 40])
                    array_line.append(distance[n + 32])
                    array_line.append(distance[n + 24])
                    array_line.append(distance[n + 16])
                    array_line.append(distance[n + 8])
                    array_line.append(distance[n])
                        # array_line.append(distance[1 + 56 - 8*k])
                        # array_line.append(distance[0 + 56 - 8*k])
                        # array_line.append(distance[3 + 56 - 8*k])
                        # array_line.append(distance[2 + 56 - 8*k])
                        # array_line.append(distance[5 + 56 - 8*k])
                        # array_line.append(distance[4 + 56 - 8*k])
                        # array_line.append(distance[7 + 56 - 8*k])
                        # array_line.append(distance[6 + 56 - 8*k])
                #     # for n in range(4):
                #         # array_line.append(distance[3 - n + 56 - 8*k])
                #     # for n in range(4):
                #         # array_line.append(distance[7 - n + 56 - 8*k])
                    distance_array.append(array_line)
                ellapsed = time.ticks_diff(time.ticks_ms(), t0)
                synapse.publish('range_array', distance_array, 'range_array')
                await asyncio.sleep_ms(int(1000./self.sampling_freq) - ellapsed)
            await asyncio.sleep_ms(2)

    def _reorder_8x8_array(self, distances):
        new_array = []
        for k in range(8):
            for n in range(4):
                new_array.append(distances[3 - n + 56 - 8*k])
            for n in range(4):
                new_array.append(distances[7 - n + 56 - 8*k])

        return new_array


