#!/usr/bin/python

# Copyright Skullspace, 2014
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved. This file is offered as-is,
# without any warranty.
# http://www.gnu.org/prep/maintain/html_node/License-Notices-for-Other-Files.html
# @author Jay Smith <jayvsmith@gmail.com>

from buzz import buzz
import RPi.GPIO as GPIO

# Mapping GIPO pins to player IDs
pin_table = {17: -1, 18: 0, 27: 1, 22: 2} 

def button_pressed(pin):
    buzz(pin_table[pin])

def main():
    GPIO.setmode(GPIO.BCM)

    # Pull pins to GND to trigger the interrupt
    for pin in pin_table:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.FALLING,
                              callback=button_pressed, bouncetime=300)
    try:
        while True: pass
    except:
        GPIO.cleanup() # Clean up on CTRL+C

if __name__ == "__main__":
    main()

