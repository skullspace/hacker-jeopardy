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

class _PygameAudio(_NoAudio):
    def __init__(self):
        pygame.mixer.init()
        buzz_path = config.get("audio", "player_buzzed")
        wrong_answer_path = config.get("audio", "wrong_answer")
        everybody_wrong_path = config.get("audio","all_wrong")

        self.player_buzz = pygame.mixer.Sound(buzz_path)
        self.wrong_answer = pygame.mixer.Sound(wrong_answer_path)
        self.all_wrong = pygame.mixer.Sound(everybody_wrong_path)

    def beep_for_player(self, i):
        self.player_buzz.play()

    def wrong(self):
        self.wrong_answer.play()

    def everybody_wrong(self):
        self.all_wrong.play()

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
