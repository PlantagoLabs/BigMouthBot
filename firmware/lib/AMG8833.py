from machine import I2C, Pin

class AMG8833:
    # based on https://github.com/bkircher67/Simple-Micropython-Class-for-Controlling-AMG8833-8x8-Pixel-Grid-Eye-/blob/master/AMG8833.py
    normal_mode  = 0x00
    sleep_mode  = 0x00
    standby_mode_60 = 0x20
    standby_mode_10 = 0x21

    def __init__(self, i2c, addr=0x69):
        """
        initialization of class, requires 2 parameters

        parameters:
            i2c (initialized bus eg. with i2c = machine.I2C(sda=.., scl=...))
            addr  address of AMG88332 (in general 0x69 = 105d)
        """
        self._i2c = i2c
        self._addr = addr
        a = self._i2c.scan()
        if not self._addr in a:
            print("no device on selected address %02X!" % self._addr)
        else:
            print("device on address %02X available." % self._addr)


    def set_power_mode(self, mode):
        """

        """
        b = bytes([mode])
        self._i2c.writeto_mem(self._addr, 0x00, b)
        return True

    def temperature(self):
        """
        receive the current temperature in degree celcius

        tempearture as float
        """
        t = self._i2c.readfrom_mem(self._addr, 0x0E, 2)
        return (t[0] + t[1]*256) * 0.0625
    
    def raw_to_celcius(self, raw_val):
        return 0.25*raw_val


    def read_grid(self):
        """
        read grid data from the chip 
        (starting address 0x80, )

        parameter: none (i2c and address are object properties)

        return 8x8 grid of INTEGER Values (no calculation) of real temperature
        """
        bin_data = list(self._i2c.readfrom_mem(self._addr, 0x80, 128)) # linear data 128 byte
        float = [self.raw_to_celcius(256*hi + lo) for lo,hi in zip(bin_data[::2],bin_data[1::2])] # linear data 64 Integer
        return [float[i:i+8] for i in range(0, 64, 8)] # 8x8 data structure


    def print8x8(self, data8x8):
        """
        simple support routine to show the 8x8 values

        parameter:
            data8x8 ... data provided as 8x8 array

        return NONE
        """
        average = 0
        for row in data8x8:
            for item in row:
                average += item/64.

        for row in data8x8:
            for item in row:
                if item > average:
                    print('x', end=' ')
                else:
                    print(' ', end=' ')
            print()