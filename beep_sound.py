from os import system, getenv
from os.path import exists, join

BEEP_COMMAND = 'beep'

beep_table = {
    -1: (1, 250, 200),
    0: (1, 300, 440),
    1: (2, 100, 440),
    2: (3, 75, 440) }

def command_exists(cmd):
    return any( exists(join(pth, cmd))
                for pth in getenv('PATH').split(':') )

def beep_for_player(i):
    if command_exists(BEEP_COMMAND):
        r, l, f = (
        (i+1, beep_table[2][1], beep_table[2][2])
        if i not in beep_table else beep_table[i] )
        system("%s -r %s -l %s -f %s" % (BEEP_COMMAND, r, l, f) )
