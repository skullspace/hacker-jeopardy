#!/usr/bin/env python

# debug tool for figuring out what your current screen size is

import curses

def main(screen):
    return screen.getmaxyx()
    
if __name__=='__main__':
    height, width = curses.wrapper(main)
    print "%s, %s" % (width, height),
