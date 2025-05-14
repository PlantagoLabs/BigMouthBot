# Code ported from the quadrature_encoder_substep example from raspberry pi: 
# https://github.com/raspberrypi/pico-examples/tree/master/pio/quadrature_encoder_substep

import machine
import rp2
from machine import Timer, disable_irq, enable_irq
import time

class SubStepEncoder:
    _gear_ratio = (30/14) * (28/16) * (36/9) * (26/8) # 48.75
    _counts_per_motor_shaft_revolution = 12
    resolution = _counts_per_motor_shaft_revolution * _gear_ratio # 585

    def __init__(self, index, encAPin, encBPin, flip_dir=False, estimator_freq=100, time_to_stop_ms = 500):
        self.flip_dir = flip_dir 
        self.clocks_per_us = (machine.freq()) / 1000000
        print(self.clocks_per_us)
        self.time_to_stop_us = time_to_stop_ms*1000

        self.calibration = [0, 64, 128, 192]
        
        if(abs(encAPin - encBPin) != 1):
            raise Exception("Encoder pins must be successive!")
        basePin = machine.Pin(min(encAPin, encBPin))
        secondPin = machine.Pin(max(encAPin, encBPin))
        self.sm = rp2.StateMachine(index, self._encoder, in_base=basePin)
        # self.sm.active(0)

        # set up status to be rx_fifo < 1
        # section 3.7, page 369 of rp2040 datasheet
        machine.mem32[0x502000CC] = ((machine.mem32[0x502000CC] & 0xFFFFFF80) | 0x12)

        irq_state = disable_irq()
        pin_state = secondPin.value()*2 + basePin.value()
        self.sm.exec(f"set(y, {pin_state})")
        self.sm.exec("mov(osr, y)")

        position = 0
        if pin_state == 0:
            position = 0
        elif pin_state == 0:
            position = 3
        elif pin_state == 0:
            position = 1
        else: 
            position = 2

        self.sm.exec(f"set(y, {position})")
        self.sm.active(1)

        enable_irq(irq_state)
        
        self.steps = 0
        self.cycles = 0
        self.prev_read_timetick = time.ticks_us()
        self.prev_transition_timetick = time.ticks_us()
        self.previous_transition_steps = 0
        self.moving_forward = 0
        self.stopped = True
        self.encoder_speed = 0.0
        self.delta_t_prediction = 0
        self.delta_step = 0.0

        self.estimator_freq = estimator_freq
        self.updateTimer = Timer()
        self.updateTimer.init(freq=estimator_freq, callback=lambda t:self._encoder_get_counts_from_pio())

    def get_wheel_speed(self):
        return self.encoder_speed/self.resolution

    def get_encounter_counts(self):
        return (self.steps, self.cycles, self.prev_read_timetick, self.moving_forward, self.prev_transition_timetick, self.encoder_speed/self.resolution)

    def _encoder_get_counts_from_pio(self):
        num_pairs = self.sm.rx_fifo()>>1

        if not num_pairs:
            return 

        irq_state = disable_irq()

        while num_pairs > 0:
            self.cycles = self.sm.get()
            new_steps  = self.sm.get()
            num_pairs -= 1

        enable_irq(irq_state)

        time.sleep_us(2)

        num_pairs = self.sm.rx_fifo()>>1

        if not num_pairs:
            return 

        irq_state = disable_irq()

        t0 = time.ticks_us()

        while num_pairs > 0:
            self.cycles = self.sm.get()
            new_steps  = self.sm.get()
            num_pairs -= 1

        t1 = time.ticks_us() 

        enable_irq(irq_state)

        new_read_timetick = time.ticks_add(t0, (time.ticks_diff(t1, t0)) >> 2 )

        if new_steps > 0x80000000:
            new_steps = int(new_steps - 0xFFFFFFFF)

        if self.cycles > 0x80000000:
            self.cycles = int(0xFFFFFFFF - self.cycles)
            self.moving_forward = 1
        else:
            self.cycles = int(0x80000000 - self.cycles)
            self.moving_forward = 0

        new_transition_timetick = time.ticks_add(new_read_timetick, int((self.cycles*-13)//self.clocks_per_us) )

        # check if stopped
        if self.steps == new_steps:
            if time.ticks_diff(new_read_timetick, self.prev_read_timetick) > self.time_to_stop_us:
                self.encoder_speed = 0.0
                self.stopped = True
        else:
            self.prev_read_timetick = new_read_timetick

        # if there is a transition, compute speed
        if self.steps != new_steps:
            transition_steps = new_steps
            if not self.stopped and time.ticks_diff(new_transition_timetick, self.prev_transition_timetick) > 0:
                new_speed = 1e6*(transition_steps - self.previous_transition_steps)/time.ticks_diff(new_transition_timetick, self.prev_transition_timetick)
                new_speed = 0.5*self.encoder_speed + 0.5*new_speed
                self.encoder_speed = new_speed
            self.stopped = False
            self.previous_transition_steps = transition_steps
            self.prev_transition_timetick = new_transition_timetick

        # if not stopped, estimate current position
        if not self.stopped:
            self.delta_t_prediction = 1e-6*time.ticks_diff(new_read_timetick, self.prev_transition_timetick)
            self.delta_step = self.encoder_speed*self.delta_t_prediction

            if self.delta_step > 1.0:
                self.steps = self.previous_transition_steps + 1.0
                self.encoder_speed = 1.0/self.delta_t_prediction
            elif self.delta_step < -1.0:
                self.steps = self.previous_transition_steps - 1.0
                self.encoder_speed = -1.0/self.delta_t_prediction
            else:
                self.steps = self.previous_transition_steps + self.delta_step
        

    @rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, out_shiftdir=rp2.PIO.SHIFT_RIGHT, autopush=True)
    def _encoder():
        in_(x, 32)
        in_(y, 32)

        label("update_state")
        out(isr, 2)
        in_(pins, 2)
        mov(osr, invert(isr))
        mov(pc, osr)

        label("decrement")
        jmp(y_dec, "decrement_cont")
        label("decrement_cont")
        set(x, 1)
        mov(x, reverse(x))

        label("check_fifo")
        wrap_target()
        jmp(x_dec, "check_fifo_cont")
        label("check_fifo_cont")
        mov(pc, invert(status))

        label("increment")
        mov(y, invert(y))
        jmp(y_dec, "increment_cont")
        label("increment_cont")
        mov(y, invert(y))
        set(x, 0)
        wrap()

        label("invalid")
        jmp("update_state")

        jmp("invalid")
        jmp("increment")    [0]
        jmp("decrement")    [1]
        jmp("check_fifo")   [4]

        jmp("decrement")    [1]
        jmp("invalid")
        jmp("check_fifo")   [4]
        jmp("increment")    [0]

        jmp("increment")    [0]
        jmp("check_fifo")   [4]
        jmp("invalid")
        jmp("decrement")    [1]

        jmp("check_fifo")   [4]
        jmp("decrement")    [1]
        jmp("increment")    [0]
        jmp("update_state") [1]



	
   