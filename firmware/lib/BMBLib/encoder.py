# Modified from XRPLib
# from XRPLib: Modified from https://forum.micropython.org/viewtopic.php?t=12277&p=66659

import machine
import rp2
from machine import Timer

class Encoder:
    _gear_ratio = (30/14) * (28/16) * (36/9) * (26/8) # 48.75
    _counts_per_motor_shaft_revolution = 12
    resolution = _counts_per_motor_shaft_revolution * _gear_ratio # 585
    
    def __init__(self, index, encAPin, encBPin, flip_dir=False, estimator_freq=50):
        """
        Uses the on board PIO State Machine to keep track of encoder positions. 
        Only 4 encoders can be instantiated this way.
        
        :param index: The index of the state machine to be used, indexed 0-3.
        :type index: int
        :param encAPin: The pin the left reflectance sensor is connected to
        :type encAPin: int
        :param encBPin: The pin the right reflectance sensor is connected to
        :type encBPin: int
        """
        self.flip_dir = flip_dir 
        
        if(abs(encAPin - encBPin) != 1):
            raise Exception("Encoder pins must be successive!")
        basePin = machine.Pin(min(encAPin, encBPin))
        self.sm = rp2.StateMachine(index, self._encoder, in_base=basePin)
        self.reset_encoder_position()
        self.sm.active(1)
        
        self.encoder_speed = 0 #rpm
        self.previous_encoder_position = 0
        self.estimator_freq = estimator_freq
        self.updateTimer = Timer()
        self.updateTimer.init(freq=estimator_freq, callback=lambda t:self._compute_speed())
    
    def reset_encoder_position(self):
        """
        Resets the encoder position to 0
        """
        # It's possible for this to cause issues if in the middle of inrementing
        # or decrementing, but the result should only be off by 1. If that's a
        # problem, an alternative solution is to stop the state machine, then
        # reset both x and the program counter. But that's excessive.
        self.previous_encoder_position = 0
        self.sm.exec("set(x, 0)")
    
    def get_encoder_position(self):
        """
        :return: The position of the encoded motor, in counts, relative to the last time reset was called.
        :rtype: int
        """
        # Read 5 times for it to get past the buffer
        counts = self.sm.get()
        counts = self.sm.get()
        counts = self.sm.get()
        counts = self.sm.get()
        counts = self.sm.get()
        if(counts > 2**31):
            counts -= 2**32
        if self.flip_dir:
            return -counts
        return counts
    
    def get_motor_position(self):
        """
        :return: The position of the motor shaft, in revolutions, relative to the last time reset was called.
        :rtype: float
        """
        return self.get_encoder_position() / self._counts_per_motor_shaft_revolution
        
    def get_wheel_position(self):
        """
        :return: The position of the wheel, in revolutions, relative to the last time reset was called.
        :rtype: float
        """
        return self.get_encoder_position() / self.resolution
        
    def get_encoder_speed(self):
        return self.encoder_speed
        
    def get_motor_speed(self):
        return self.encoder_speed/self._counts_per_motor_shaft_revolution
        
    def get_wheel_speed(self):
        return self.encoder_speed/self.resolution
        
    def _compute_speed(self):
        new_encoder_position = self.get_encoder_position()
        self.encoder_speed = (self.encoder_speed + (new_encoder_position - self.previous_encoder_position)*self.estimator_freq)>>1
        if self.encoder_speed == -1: # due to how python handles negative numbers
            self.encoder_speed = 0
        self.previous_encoder_position = new_encoder_position
        

    @rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, out_shiftdir=rp2.PIO.SHIFT_RIGHT)
    def _encoder():
        # Register descriptions:
        # X - Encoder count, as a 32-bit number
        # OSR - Previous pin values, only last 2 bits are used
        # ISR - Push encoder count, and combine pin states together
        
        # Jump table
        # The program counter is moved to memory address 0000 - 1111, based
        # on the previous (left 2 bits) and current (right  bits) pin states
        jmp("read") # 00 -> 00 No change, continue
        jmp("decr") # 00 -> 01 Reverse, decrement count
        jmp("incr") # 00 -> 10 Forward, increment count
        jmp("read") # 00 -> 11 Impossible, continue
        
        jmp("incr") # 01 -> 00 Forward, increment count
        jmp("read") # 01 -> 01 No change, continue
        jmp("read") # 01 -> 10 Impossible, continue
        jmp("decr") # 01 -> 11 Reverse, decrement count
        
        jmp("decr") # 10 -> 00 Reverse, decrement count
        jmp("read") # 10 -> 01 Impossible, continue
        jmp("read") # 10 -> 10 No change, continue
        jmp("incr") # 10 -> 11 Forward, increment count
        
        jmp("read") # 11 -> 00 Impossible, continue
        jmp("incr") # 11 -> 01 Forward, increment count
        jmp("decr") # 11 -> 10 Reverse, decrement count
        jmp("read") # 11 -> 11 No change, continue
        
        label("read")
        mov(osr, isr)   # Store previous pin states in OSR
        mov(isr, x)     # Copy encoder count to ISR
        push(noblock)   # Push count to RX buffer, and reset ISR to 0
        out(isr, 2)     # Shift previous pin states into ISR
        in_(pins, 2)    # Shift current pin states into ISR
        mov(pc, isr)    # Move PC to jump table to determine what to do next
        
        label("decr")           # There is no explicite increment intruction, but X can be
        jmp(x_dec, "decr_nop")  # decremented in the jump instruction. So we use that and jump
        label("decr_nop")       # to the next instruction, which is equivalent to just decrementing
        jmp("read")
        
        label("incr")           # There is no explicite increment intruction, but X can be
        mov(x, invert(x))       # decremented in the jump instruction. So we invert X, decrement, 
        jmp(x_dec, "incr_nop")  # then invert again - this is equivalent to incrementing.
        label("incr_nop")
        mov(x, invert(x))
        jmp("read")
        
        # Fill remaining instruction memory with jumps to ensure nothing bad happens
        # For some reason, weird behavior happens if the instruction memory isn't full
        jmp("read")
        jmp("read")
        jmp("read")
        jmp("read")