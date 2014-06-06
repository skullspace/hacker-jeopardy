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

import curses, json, sys
from curses import wrapper

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

with open('buzzin') as f:
    player_names = tuple( player_name.strip()
                          for player_name in f )

def run_questions_menu(screen, questions, answered_questions):
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

            if run_question(
                screen,
                questions[selected_question[0]]["questions"][
                    selected_question[1]//100-1]["question"] ):
                
                answered_questions.add( tuple(selected_question) )

        draw_window_grid_and_refresh(
            screen, questions, selected_question, answered_questions)

def run_question(screen, question):
    draw_window_question_prompts_and_refresh(
        screen, prompt_buzz_enable, False, False, question)

    question_attempted = False

    while True:
        event = screen.getch()

        if event == ord('s'):
            run_buzzin_attempts(screen, question)
            question_attempted = True
            break

        elif event == ord(" "):
            break

    return question_attempted

# main game loop
def main(screen):
    screen.keypad(1)
    
    # initialize colours
    init_colors()

    draw_splash(screen)
    screen.getch()
    screen.clear()    

    with open(questions_file) as f:
        questions = json.load(f)

    answered_questions = set()

    run_questions_menu(screen, questions, answered_questions)
    screen.clear()

# get the buzzed in player name
def run_buzzin_attempts(screen, question):
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

        # if all the players have had a chance
        if len(players_allowed) == 1:
            break

def run_wait_for_right_wrong(screen):
    while True:
        event = screen.getch()
        
        if event == ord('r'):
            return True
        elif event == ord('w'):
            return False

if __name__=='__main__':
    curses.wrapper(main)
