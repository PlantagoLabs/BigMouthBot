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

    def __init__(self, index, encAPin, encBPin, flip_dir=False, estimator_freq=100):
        self.flip_dir = flip_dir 
        
        if(abs(encAPin - encBPin) != 1):
            raise Exception("Encoder pins must be successive!")
        basePin = machine.Pin(min(encAPin, encBPin))
        secondPin = machine.Pin(max(encAPin, encBPin))
        self.sm = rp2.StateMachine(index, self._encoder, in_base=basePin)
        # self.sm.active(0)

        # set up status to be rx_fifo < 1
        # section 3.7, page 369 of rp2040 datasheet
        machine.mem32[0x502000CC] = ((machine.mem32[0x502000CC] & 0xFFFFFF80) | 0x12)
        print(hex(machine.mem32[0x502000CC]))

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
        self.num_pairs = 0
        self.num_iter = 0
        self.rx_fifo = 0
        self.read_timeticks = time.ticks_us()

        self.estimator_freq = estimator_freq
        self.updateTimer = Timer()
        self.updateTimer.init(freq=estimator_freq, callback=lambda t:self._encoder_get_counts_from_pio())

    def get_encounter_counts(self):
        return (self.steps, self.cycles, self.read_timeticks, self.num_pairs, self.num_iter, self.rx_fifo)

    def _encoder_get_counts_from_pio(self):
        self.rx_fifo = self.sm.rx_fifo()
        num_pairs = self.sm.rx_fifo()>>1
        self.num_pairs += num_pairs

        irq_state = disable_irq()

        while num_pairs > 0:
            self.cycles = self.sm.get()
            self.steps  = self.sm.get()
            num_pairs -= 1

        self.num_iter += 1

        self.read_timeticks = time.ticks_us()

        enable_irq(irq_state)

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



	
   