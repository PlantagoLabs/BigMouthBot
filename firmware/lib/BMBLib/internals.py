from machine import ADC
import uasyncio
import time

class BatteryMonitor:
    def __init__(self, period_ms = 5):
        self.period_ms = period_ms
        self.adc = ADC(28)
        self.v_batt = 4
        self.adc_to_voltage = 4.0303*3.3/65535.0
        self.sampler_task = uasyncio.create_task(self._battery_sampling())
        
    async def _battery_sampling(self):
        while 1:
            self.v_batt = ((7*self.v_batt) + self.adc.read_u16())>>3
            await uasyncio.sleep_ms(self.period_ms)
            
    def get_battery_voltage(self):
        return self.adc_to_voltage*self.v_batt
            
        
        
        
    