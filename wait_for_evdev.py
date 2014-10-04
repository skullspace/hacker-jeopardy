#!/usr/bin/env python

# Copyright Skullspace, 2014
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved. This file is offered as-is,
# without any warranty.
# http://www.gnu.org/prep/maintain/html_node/License-Notices-for-Other-Files.html
# @author Mark Jenkins <mark@markjenkins.ca>

# Instructions
# everything except step 2) as root here
# (unless you want to master udev...)

# 1) Install https://pythonhosted.org/evdev/install.html
# $ easy_install evdev
# (or if you're like me, easy_install --prefix=/opt/python-evdev with
# PYTHONPATH set as needed)

# 2) use xinput to disable any keyboards, mice or pedals that are for buzing,
# not for using with X

# 3) figure out which ev numbers from /dev/input/event? you want to work with
# by using cat

# 4) call this program with the device node

from sys import argv
import time

from evdev import InputDevice

from buzz import buzz


def main():
    dev = InputDevice(argv[1])
    buzz_id = int(argv[2])

    buzzed_at = 0

    for i, event in enumerate(dev.read_loop()):
        print i
        now_time = time.time()
        if buzz_id != -1 or now_time - buzzed_at >= 2:
            buzz(buzz_id)
            buzzed_at = now_time
if __name__ == "__main__":
    main()
