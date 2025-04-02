from machine import Pin
import time

user_button = Pin(22, mode=Pin.IN)

print(user_button.value())
time.sleep(0.05)

if user_button.value():
    import test_setup
else:
    print('User button pressed: not running app')

