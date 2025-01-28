from machine import Timer

class BasicControl:
    def __init__(self, measure_func, command_func, freq:int=50):
        self.Kp = None
        self.Ki = None
        self.Ilimit = None
        self.Kd = None
        
        self.measure_func = measure_func
        self.command_func = command_func
        self.freq = freq
        
        self.updateTimer = Timer()
        self.updateTimer.init(freq=freq, callback=lambda t:self._update())
        
        self.target = None
        self.command = None

        self.Ipos = 0
        self.Ineg = 0
        self.prev_error = 0
        
    def set_target(self, target):
        self.target = target
        self.command = None

    def force_command(self, command):
        self.command = command

    def set_proportional_gain(self, Kp):
        self.Kp = Kp
        
    def set_integrator_gain(self, Ki, Ilimit):
        self.Ki = Ki
        self.Ilimit = Ilimit
        self.Ipos = 0
        self.Ineg = 0
        
    def _add_error_to_integrator(self, integrator, err):
        integrator += err
        
        if integrator > self.Ilimit:
            integrator = self.Ilimit
        elif integrator < -self.Ilimit:
            integrator = -self.Ilimit
            
        return integrator
        
    def _update(self):
        if self.command is not None:
            self.command_func(self.command)
            return

        if self.target is None:
            return
        
        err = self.target - self.measure_func()
        
        feedback = 0

        if self.Kp:
            feedback += self.Kp*err
            
        if self.Ki:
            if self.target >= 0:
                self.Ipos = self._add_error_to_integrator(self.Ipos, err)
                feedback += self.Ki*self.Ipos
            else:
                self.Ineg = self._add_error_to_integrator(self.Ineg, err)
                feedback += self.Ki*self.Ineg
                
            
                
        self.command_func(self.target + feedback)
        
    
    