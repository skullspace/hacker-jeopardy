# Copyright Skullspace, 2014
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved. This file is offered as-is,
# without any warranty.
# http://www.gnu.org/prep/maintain/html_node/License-Notices-for-Other-Files.html
# @author Jay Smith <jayvsmith@gmail.com>

import ConfigParser
from os import system, getenv
from os.path import exists, join

try:
    import pygame
except ImportError:
    pass

config = ConfigParser.ConfigParser()
config.read("config.ini")

class _NoAudio(object):
    def beep_for_player(self, i):
        return
    def everybody_wrong(self):
        return
    def wrong(self):
        return
    def correct(self):
        return
    def final_question(self):
        return

class _PygameAudio(_NoAudio):
    def __init__(self):
        pygame.mixer.init()
        buzz_path = config.get("audio", "player_buzzed")
        wrong_answer_path = config.get("audio", "wrong_answer")
        everybody_wrong_path = config.get("audio","all_wrong")
        correct_answer_path = config.get("audio", "correct_answer")
        final_question_music_path = config.get("audio", "final_question_music")

        self.player_buzz = pygame.mixer.Sound(buzz_path)
        self.wrong_answer = pygame.mixer.Sound(wrong_answer_path)
        self.all_wrong = pygame.mixer.Sound(everybody_wrong_path)
        self.correct_answer = pygame.mixer.Sound(correct_answer_path)
        self.final_question_music = \
            pygame.mixer.Sound(final_question_music_path)

    def beep_for_player(self, i):
        self.player_buzz.play()
    def wrong(self):
        self.wrong_answer.play()
    def everybody_wrong(self):
        self.all_wrong.play()
    def correct(self):
        self.correct_answer.play()
    def final_question(self):
        self.final_question_music.play()

class _BeepAudio(_NoAudio):
    def __init__(self, beep_command):
        self.beep_table = {
            -1: (1, 250, 200),
            0: (1, 300, 440),
            1: (2, 100, 440),
            2: (3, 75, 440)}
        self.beep_command = beep_command

    def beep_for_player(self, i):
        r, l, f = ((i+1, self.beep_table[2][1], self.beep_table[2][2])
                   if i not in self.beep_table
                   else self.beep_table[i])
        system("%s -r %s -l %s -f %s" % (self.beep_command, r, l, f))

    def everybody_wrong(self):
        self.beep_for_player(-1)

    def final_question(self):
        # playing a full musical piece with PC speaker beeping would be pretty
        # cool, but should be done with library, not command execution
        pass

def command_exists(cmd):
    return any(exists(join(pth, cmd))
               for pth in getenv('PATH').split(':'))

def build_audio_engine():
    selected_engine = config.get("audio", "engine")
    beep_command = config.get("audio", "beep_command")

    if selected_engine == "pygame":
        return _PygameAudio()
    elif selected_engine == "beep" and command_exists(beep_command):
        return _BeepAudio(beep_command)
    else:
        return _NoAudio()

