from machine import Pin, ADC

_leftReflectance = ADC(Pin(26))
_rightReflectance = ADC(Pin(27))

def get_left_reflectance():
    return _leftReflectance.read_u16()/65536.

def get_right_reflectance():
    return _rightReflectance.read_u16()/65536.