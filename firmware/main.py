from machine import Pin
import sys
import time

user_button = Pin(22, mode=Pin.IN)

time.sleep(0.05)

if user_button.value():
    try:
        from BMBLib import setup
        import explore
    except Exception as e: 
        sys.print_exception(e)
        with open('traceback.txt', 'w') as fid:
            sys.print_exception(e, fid)
        print('Initiating shutdown')
        setup.drivetrain.stop()
        setup.servo_1.free()
        print('Done')
else:
    print('User button pressed: not running app')

