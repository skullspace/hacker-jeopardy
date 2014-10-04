#!/bin/sh

./wait_for_evdev.py $1 $2
beep  -f 300 -r 6
