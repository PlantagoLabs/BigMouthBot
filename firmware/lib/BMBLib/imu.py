import asyncio
from LSM6DSO import LSM6DSO
from BMBLib import synapse
from BMBLib import profiler

class LSM6DSOIMU:
    def __init__(self, i2c, period_ms, start_stopped = True):
        self.imu = LSM6DSO(i2c)
        self.stopped = start_stopped
        self.gyro_calibration = [0, 0, 0]
        self.num_calibration = 0
        self.period_ms = period_ms
        
        synapse.apply('drivetrain.stopped', self._act_stopped_state)
        self.sampler_task = asyncio.create_task(self._sample_imu())

    def _act_stopped_state(self, state):
        self.stopped = state

    @profiler.profile("imu.read")
    def _read_imu(self):
        return self.imu.get_dict()

    async def _sample_imu(self):
        while 1:
            data = self._read_imu()

            if self.stopped:
                self.num_calibration += 1
                if self.num_calibration > 30:
                    self.num_calibration = 30
                filter_coef = 1.0/self.num_calibration
                for k in range(3):
                    self.gyro_calibration[k] = (1-filter_coef)*self.gyro_calibration[k] + filter_coef*data['gyro'][k]

            for k in range(3):
                data['gyro'][k] -= self.gyro_calibration[k]
            synapse.publish('imu', data, 'imu')

            await asyncio.sleep_ms(self.period_ms)