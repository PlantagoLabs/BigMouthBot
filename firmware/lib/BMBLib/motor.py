# Modified from XRPLib

from machine import Pin, PWM
class Motor:

    """
    A wrapper class handling direction and power sets for DC motors on the XRP robots
    """

    def __init__(self, direction_pin: int, speed_pin: int, flip_dir:bool=False, motor_model = None, voltage_func = None):
        """
        Initializes motor driver class
        
        Arguments are:
        - direction_pin: pin that sets the direction of the motor
        - speed_pin: pin on which the motor PWM will be applied
        - flip_dir: bool to flip the direction of rotation for positive effort/voltage/speed. Default is False
        - motor_model: a list of length 4 that is obtained during motor calibration. Needed to use the set_speed function. Default is None
        - voltage_func: a function that returns the max voltage applied to the motors. needed for set_speed and set_voltage functions. default is None
        """
        self._dirPin = Pin(direction_pin, Pin.OUT)
        self._speedPin = PWM(Pin(speed_pin, Pin.OUT))
        self._speedPin.freq(150)
        self.flip_dir = flip_dir
        self.motor_model = motor_model
        self.voltage_func = voltage_func
        self._MAX_PWM = 65534 # Motor holds when actually at full power

    def set_effort(self, effort: float):
        """
        Sets the effort value of the motor (corresponds to power)

        :param effort: The effort to set the motor to, between -1 and 1
        :type effort: float
        """

        if effort < 0:
            # Change direction if negative power
            effort *= -1
            self._set_direction(1)
        else:
            self._set_direction(0)
        # Cap power to [0,1]
        effort = max(0,min(effort,1))
        self._speedPin.duty_u16(int(effort*self._MAX_PWM))
        
    def set_voltage(self, voltage: float):
        """
        Applies some voltage on the motor

        - voltage: Float, the average voltage applied to the motor. Negative values make the motor spin in the other direction
        """
        self.set_effort (voltage/self.voltage_func())
        
    def set_speed(self, speed: float, forward: bool = None):
        """
        Applies the right voltage on the motor to achieve some speed, based on the motor_model
        
        The target speed is achieved using open loop model.
        - speed: Float, the definition and units depend on the motor_model provided
        """
        if forward is None:
            if speed > 0.0:
                forward = True
            else:
                forward = False

        if speed == 0.0:
            voltage = 0
        else:
            if forward:
                voltage = speed/self.motor_model[1][0] + self.motor_model[1][1]
            else:
                voltage = speed/self.motor_model[0][0] + self.motor_model[0][1]
                

                
            
        self.set_voltage(voltage)

    def _set_direction(self, direction: int):
        if self.flip_dir:
            self._dirPin.value(not direction)
        else:
            self._dirPin.value(direction)
