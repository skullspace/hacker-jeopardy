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

import curses, json
from curses import wrapper
from pickle import dump, load
from os.path import exists

# from this project
from wait_4_buzz import wait_4_buzz
from curses_drawing import \
    (draw_window_grid_and_refresh, waiting_for_buzz_prompt,
     prompt_buzz_enable, prompt_right_answer,
     draw_window_question_prompts_and_refresh,
     init_colors, draw_splash, 
     )

NOBODY_BUZZED = -1

questions_file = 'questions.json'
PERSIST_FILE = 'database.pickle'

with open('buzzin') as f:
    player_names = tuple( player_name.strip()
                          for player_name in f )

def run_questions_menu(screen, questions, answered_questions, scores):
    selected_question = [0, 100]

    # initialize selected question bounds
    max_question = int(len(questions[0]["questions"]) * 100)
    max_category = len(questions) - 1

    draw_window_grid_and_refresh(
        screen, questions, selected_question, answered_questions)

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
                selected_question_dict["question"],
                selected_question_dict["answer"],
                0, # FIXME with real score
                selected_question, answered_questions, scores
                )
                
        draw_window_grid_and_refresh(
            screen, questions, selected_question, answered_questions)

def run_question(
    screen, question, answer, question_score, 
    selected_question, answered_questions, scores):
    draw_window_question_prompts_and_refresh(
        screen, prompt_buzz_enable, False, False, question)

    while True:
        event = screen.getch()

        if event == ord('s'):
            answered_questions.add( tuple(selected_question) )
            save_database(answered_questions, scores)
            run_buzzin_attempts(screen, question, answer, question_score,
                                answered_questions, scores)
            return True

        elif event == ord(" "):
            return False

def main(screen):
    screen.keypad(1)
    
    # initialize colours
    init_colors()

    draw_splash(screen)
    screen.getch()
    screen.clear()    

    with open(questions_file) as f:
        questions = json.load(f)

    answered_questions, scores = load_database(questions)

    run_questions_menu(screen, questions, answered_questions, scores)
    screen.clear()

# get the buzzed in player name
def run_buzzin_attempts(
    screen, question, answer, question_score,
    answered_questions, scores):
    correct_answer = False
    incorrect_answer = False

    players_allowed = set(
        (NOBODY_BUZZED,) + 
        tuple( range(len(player_names)) ))

    # should draw something to show our readyness for buzzing

    while True:
        draw_window_question_prompts_and_refresh(
            screen, waiting_for_buzz_prompt,
            correct_answer, incorrect_answer, question)

        buzzed_in_player_id = wait_4_buzz(players_allowed)

        if buzzed_in_player_id == NOBODY_BUZZED:
            break
        else: # else a real player
            players_allowed.remove(buzzed_in_player_id)

            # draw name of player and prompt re correct answer
            draw_window_question_prompts_and_refresh(
                screen, prompt_right_answer,
                False, False, question,
                player_names[buzzed_in_player_id] )

            correct_answer = run_wait_for_right_wrong(screen)
            incorrect_answer = not correct_answer
            if correct_answer:
                break
            
        # if all the players have had a chance
        if len(players_allowed) == 1:
            break
    
    if not correct_answer:
        draw_window_question_prompts_and_refresh(
            screen, lambda *x: None,
            False, True, answer )
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
        scores = [0,] * len(player_names)
    else:
        with open(PERSIST_FILE) as f:
            attempted_questions, scores = load(f)

    return attempted_questions, scores

def save_database(attempted_questions, scores):
    with open(PERSIST_FILE, 'w') as f:
        dump( (attempted_questions, scores), f )

if __name__=='__main__':
    curses.wrapper(main)
