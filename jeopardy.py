#!/usr/bin/env python

# Copyright Skullspace, 2014
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved. This file is offered as-is,
# without any warranty.
# http://www.gnu.org/prep/maintain/html_node/License-Notices-for-Other-Files.html
# @author Jeremy Hiebert <jkhiebert@gmail.com>
# @author Mark Jenkins <mark@markjenkins.ca>

import curses, json, time, ConfigParser
from curses import wrapper
from pickle import dump, load
from os.path import exists
from os import devnull
import sys

# from this project
from wait_4_buzz import wait_4_buzz
from curses_drawing import \
    (draw_window_grid_and_refresh,
     draw_window_question_prompts_and_refresh,
     init_colors, draw_splash,
     )
from game_audio import build_audio_engine
from question_states import *
from answer_server import build_answer_server

audio = build_audio_engine()
config = ConfigParser.ConfigParser()
config.read("config.ini")

PLAYER_SCORE_SEPARATION = ":"
SHOW_CATEGORY = True
NOBODY_BUZZED = -1
# seconds how long the host must wait before revealing the question's answer
MIN_QUESTION_TIME = 2
SHOW_STANDARD_ERROR = config.getboolean("core", "show_standard_error")
QUESTIONS_FILE = config.get("core", "questions_file")
PERSIST_FILE = config.get("core", "persist_file")

def make_player_scores(player_names, scores):
    return tuple(("%s" + PLAYER_SCORE_SEPARATION + "%s") % a
                 for a in zip(player_names, scores) )

def get_player_id_codes(player_names):
    ORD_OF_ZERO = ord('0')
    # run through tuple( because range in python 3 won't return a tuple
    # but an iterator
    return tuple( range(ORD_OF_ZERO, ORD_OF_ZERO+len(player_names)) )

def edit_names(screen, player_names):
    height, width = screen.getmaxyx()

    player_codes = get_player_id_codes(player_names)
    while True:
        event = screen.getch()
        if event in player_codes:
            code = int(chr(event))
            curses.echo()
            player_names[code] = screen.getstr(height-1, 2)
            curses.noecho()
            break

def edit_scores(screen, scores):
    height, width = screen.getmaxyx()

    score_codes = get_player_id_codes(scores)
    while True:
        event = screen.getch()
        if event in score_codes:
            code = int(chr(event))
            curses.echo()
            while True:
                try:
                    scores[code] += int( screen.getstr(height-1, 2) )
                except ValueError: pass
                else:
                    curses.noecho()
                    break
            break

def run_questions_menu(screen, questions, answered_questions, player_names,
                       scores, answer_server):
    selected_question = [0, 100]

    # initialize selected question bounds
    max_question = int(len(questions[0]["questions"]) * 100)
    max_category = len(questions) - 1

    draw_window_grid_and_refresh(
        screen, questions, selected_question, answered_questions,
        make_player_scores(player_names, scores) )

    while True:
        event = screen.getch()

        if event == ord("q"):
            break
        elif event == curses.KEY_UP:
            if selected_question[1] > 100:
                selected_question[1] -= 100
        elif event == curses.KEY_DOWN:
            if selected_question[1] < max_question:
                selected_question[1] += 100
        elif event == curses.KEY_RIGHT:
            if selected_question[0] < max_category:
                selected_question[0] += 1
        elif event == curses.KEY_LEFT:
            if selected_question[0] > 0:
                selected_question[0] -= 1
        elif event == ord(" "):

            selected_question_dict = \
                questions[selected_question[0]]["questions"][
                selected_question[1]//100-1]
            run_question(
                screen,
                questions[selected_question[0]]["name"],
                selected_question_dict["question"],
                selected_question_dict["answer"],
                # documenting the silly convention here, someday this should be
                # 0 through n-1 indexed and calucated by adding 1 and multipling
                # by 100 or whatever. (change to *200 for modern jeopardy..)
                selected_question[1]*100//100,
                selected_question, answered_questions, player_names, scores,
                answer_server
                )

        elif event == ord("e"):
            edit_scores(screen, scores)
            save_database(answered_questions, player_names, scores)
        elif event == ord("n"):
            edit_names(screen, player_names)
            save_database(answered_questions, player_names, scores)

        draw_window_grid_and_refresh(
            screen, questions, selected_question, answered_questions,
            make_player_scores(player_names, scores) )

def run_question(
    screen, category, question, answer, question_score,
    selected_question, answered_questions, player_names, scores, answer_server):

    answer_server.current_answer = answer

    pre_question = (
        question if not SHOW_CATEGORY
        else "%s for %s" % (category, question_score) )

    draw_window_question_prompts_and_refresh(
        screen, pre_question,
        player_names, NOBODY_BUZZED,
        state=QUESTION_PRE_BUZZ_EXIT)

    while True:
        event = screen.getch()

        if event == ord('s'):
            answered_questions.add( tuple(selected_question) )
            save_database(answered_questions, player_names, scores)
            run_buzzin_attempts(screen, question, answer, question_score,
                                answered_questions, player_names, scores)
            return True

        elif event == ord(" "):
            return False

def main(screen):
    if not SHOW_STANDARD_ERROR:
        sys.stderr = open(devnull, 'w')

    screen.keypad(1)

    # initialize colours
    init_colors()

    draw_splash(screen)
    screen.getch()
    screen.clear()

    answer_server = build_answer_server()
    answer_server.serve_answers()

    try:
        with open(QUESTIONS_FILE) as f:
            questions = json.load(f)

        answered_questions, player_names, scores = load_database(questions)

        run_questions_menu(screen, questions, answered_questions, player_names,
                           scores, answer_server)
        screen.clear()
    finally:
        answer_server.shutdown()

# get the buzzed in player name
def run_buzzin_attempts(
    screen, question, answer, question_score,
    answered_questions, player_names, scores):
    state = QUESTION_PRE_BUZZ # was QUESTION_PRE_BUZZ_EXIT until now
    state_start_time = time.time()

    players_allowed = set(
        (NOBODY_BUZZED,) +
        tuple( range(len(player_names)) ))

    mis_buzz_players = set()

    buzzed_in_player_id = NOBODY_BUZZED

    # should draw something to show our readyness for buzzing
    while state not in END_STATES:
        previous_state = state
        player_name = ("" if buzzed_in_player_id == NOBODY_BUZZED
                       else player_names[buzzed_in_player_id] )
        draw_window_question_prompts_and_refresh(
            screen, question, player_names, buzzed_in_player_id, state=state,
            mis_buzz_players=mis_buzz_players)
        if state in STATES_WITH_BUZZ_OPEN:
            buzzed_in_player_id = wait_4_buzz(players_allowed)
            if state == QUESTION_PRE_BUZZ:
                if buzzed_in_player_id == NOBODY_BUZZED:
                    state = QUESTION_BUZZ_OPEN
                else:
                    mis_buzz_players.add(buzzed_in_player_id)
                continue # makes for less indendation below

            # everything below here is state != QUESTION_PRE_BUZZ
            # thanks to continue above
            if buzzed_in_player_id == NOBODY_BUZZED:
                # Make sure players have had some time to answer first
                if time.time() - state_start_time > MIN_QUESTION_TIME:
                    audio.everybody_wrong()
                    state = QUESTION_EVERYBODY_WRONG
            else: # else a real player
                audio.beep_for_player(buzzed_in_player_id)
                players_allowed.remove(buzzed_in_player_id)
                state = QUESTION_WAIT_ANSWER
        else:
            # only possible state we could be in, two END_STATES stop the loop
            # three apply to above if, one is never in this loop
            assert(state == QUESTION_WAIT_ANSWER)

            if run_wait_for_right_wrong(screen):
                adjust_score_and_save(
                    buzzed_in_player_id, answered_questions, player_names,
                    scores, question_score)
                state = QUESTION_ANSWERED_RIGHT
            else:
                adjust_score_and_save(
                    buzzed_in_player_id, answered_questions, player_names,
                    scores, -question_score)
                # if all the players have had a chance
                if len(players_allowed) == 1:
                    audio.everybody_wrong()
                    state = QUESTION_EVERYBODY_WRONG
                else:
                    audio.wrong()
                    state = QUESTION_BUZZ_OPEN_AFTER_WRONG

        if previous_state != state:
            state_start_time = time.time()

    draw_window_question_prompts_and_refresh(
        screen, answer, player_names, buzzed_in_player_id, state=state )
    while True:
        if screen.getch() == ord(' '):
            break

def run_wait_for_right_wrong(screen):
    while True:
        event = screen.getch()

        if event == ord('r'):
            return True
        elif event == ord('w'):
            return False

def load_database(questions):
    if not exists(PERSIST_FILE):
        attempted_questions = set()
        with open('buzzin') as f:
            player_names = list(player_name.strip() for player_name in f )
        #TODO: Combine names and scores into one datastructure
        scores = [0,] * len(player_names)
    else:
        with open(PERSIST_FILE) as f:
            attempted_questions, player_names, scores = load(f)

    return attempted_questions, player_names, scores

def adjust_score_and_save(player_id, attempted_questions, player_names,
                          scores, adj):
    scores[player_id] += adj
    save_database(attempted_questions, player_names, scores)

def save_database(attempted_questions, player_names, scores):
    with open(PERSIST_FILE, 'w') as f:
        dump( (attempted_questions, player_names, scores), f )

if __name__=='__main__':
    curses.wrapper(main)
