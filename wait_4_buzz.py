#!/usr/bin/env python

# Copyright Skullspace, 2014
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved. This file is offered as-is,
# without any warranty.
# http://www.gnu.org/prep/maintain/html_node/License-Notices-for-Other-Files.html
# @author Mark Jenkins <mark@markjenkins.ca>
# @author Jay Smith <jayvsmith@gmail.com>
# @author Sara Arenson <sara_arenson@yahoo.ca>

import socket
import time
from buzz import PORT as BUZZ_PORT

def wait_4_buzz(players_allowed_to_answer, mis_buzz_player_penalty):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', BUZZ_PORT))

    wait_start_time = time.time()

    # keep handling requests one at a time until one of them manages
    # to set the buzz_from attribute
    while True:
        data = s.recv(256)
        try:
            buzz_from = int(data)
            if (buzz_from in players_allowed_to_answer) and \
               (wait_start_time + mis_buzz_player_penalty[buzz_from]
                < time.time() ):
                s.close()
                return buzz_from
        except ValueError:
            pass

if __name__ == "__main__":
    while True:
        print wait_4_buzz([-1, 0, 1, 2]), "buzzed"
