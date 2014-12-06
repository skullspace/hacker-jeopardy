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
from random import sample, choice

# from this project
from wait_4_buzz import wait_4_buzz
from curses_drawing import \
    (draw_window_grid_and_refresh,
     draw_window_question_prompts_and_refresh,
     init_colors, draw_splash, draw_daily_double_splash,
     draw_final_jeopardy_splash,
     FINAL_STATE_BEGIN, FINAL_STATE_CATEGORY, FINAL_STATE_QUESTION,
     FINAL_STATE_GO_AROUND, FINAL_STATE_GO_AROUND_ANSWER,
     FINAL_STATE_ALL_SCORES
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

# traditionally 1 in the first round and 2 in the second, but we're only doing
# single rounds so make it two
# must not exceed the number of categories
NUM_DAILY_DOUBLES = 2

MIN_DAILY_DOUBLE_WAGER = 5
# highest category value
MAX_DAILY_DOUBLE_FOR_NEG = 500

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
            scores[code] += edit_score_prompt(screen, code)
            break

def edit_score_prompt(screen, code):
    height, width = screen.getmaxyx()

    curses.echo()
    while True:
        try:
            score_change = int( screen.getstr(height-1, 2) )
        except ValueError: pass
        else:
            curses.noecho()
            return score_change

def pick_dd_player(screen, player_names):
    height, width = screen.getmaxyx()

    player_codes = get_player_id_codes(player_names)
    while True:
        event = screen.getch()
        if event == ord(" "):
            return None
        elif event in player_codes:
            return int(chr(event))

            curses.echo()
            while True:
                try:
                    how_much = int( screen.getstr(height-1, 2) )
                except ValueError: pass
                else:
                    curses.noecho()
                    break


def input_dd_player_wager(screen, min_wager, max_wager):
    height, width = screen.getmaxyx()

    curses.echo()
    while True:
        try:
            how_much = int( screen.getstr(height-1, 2) )
        except ValueError: pass
        else:
            if min_wager <= how_much <= max_wager:
                curses.noecho()
                return how_much

def do_final_jeopardy(screen, player_names, scores):
    draw_final_jeopardy_splash(
        screen, "Final Jeopardy!", FINAL_STATE_BEGIN,
        player_names, scores)
    run_until_space(screen)
    draw_final_jeopardy_splash(
        screen, config.get("core", "final_category"), FINAL_STATE_CATEGORY,
        player_names, scores )
    run_until_space(screen)

    question = \
        open(config.get("core", "final_question_file")).readline().strip()
    answer = open(config.get("core", "final_answer_file")).readline().strip()

    draw_final_jeopardy_splash(
        screen,
        question,
        FINAL_STATE_QUESTION,
        player_names, scores )
    run_until_space(screen)

    state = FINAL_STATE_GO_AROUND
    q_or_a = question
    for score, player_code, player_name in sorted(zip(
            tuple(scores), # make a copy of scores as we're changing in place
            tuple( range(len(player_names)) ),
            player_names,
            ) ):
        if  score > 0:
            draw_final_jeopardy_splash(
                screen,
                q_or_a,
                state,
                (player_name,), (score,) )
            delta = -1
            while not (0<= delta <= score):
                delta = edit_score_prompt(screen, player_code)
            scores[player_code] += delta
            if delta > 0:
                state = FINAL_STATE_GO_AROUND_ANSWER
                q_or_a = answer
            draw_final_jeopardy_splash(
                screen,
                q_or_a,
                state,
                player_names, scores )
            run_until_space(screen)

    winning_score = max(scores)
    winners = [ player_name
                for score, player_name in zip(scores, player_names)
                if score == winning_score ]

    draw_final_jeopardy_splash(
        screen, "The winner is "+ ", ".join(winners) + "!",
        FINAL_STATE_ALL_SCORES,
        player_names, scores )
    run_until_space(screen)

    draw_final_jeopardy_splash(
        screen, "Thanks for playing. Happy Hacking!",
        FINAL_STATE_ALL_SCORES,
        player_names, scores )
    run_until_space(screen)

def run_questions_menu(screen, questions, answered_questions, player_names,
                       scores, daily_doubles, answer_server):
    number_of_rows = len(questions[0]["questions"])
    total_avail_questions = len(questions) * number_of_rows

    selected_question = [0, 100]

    # initialize selected question bounds
    max_question = number_of_rows * 100
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
            # that division arithmatic drives me nuts...
            question_cat, question_row = (
                selected_question[0], selected_question[1]//100-1)

            selected_question_dict = \
                questions[question_cat]["questions"][question_row]

            is_dd = (question_cat, question_row) in daily_doubles

            question_was_shown = run_question(
                screen,
                questions[question_cat]["name"],
                selected_question_dict["question"],
                selected_question_dict["answer"],
                is_dd,
                # documenting the silly convention here, someday this should be
                # 0 through n-1 indexed and calucated by adding 1 and multipling
                # by 100 or whatever. (change to *200 for modern jeopardy..)
                selected_question[1]*100//100,
                selected_question, answered_questions, player_names,
                scores, daily_doubles,
                answer_server
                )
            if question_was_shown:
                if is_dd:
                    daily_doubles.remove( (question_cat, question_row) )
                answered_questions.add( tuple(selected_question) )
                save_database(answered_questions, player_names,
                              scores, daily_doubles)
                # perhaps other saving could be done here and not
                # redundantly done in some of the sub-calls... but
                # remember we want to put in wrong penalities right away
                save_database(answered_questions, player_names,
                              scores, daily_doubles)

                if ( len(answered_questions) >= total_avail_questions):
                    # should never answer more questions then we have...
                    assert( len(answered_questions) == total_avail_questions)
                    do_final_jeopardy(screen, player_names, scores)
                    break

        elif event == ord("e"):
            edit_scores(screen, scores)
            save_database(answered_questions, player_names,
                          scores, daily_doubles)
        elif event == ord("n"):
            edit_names(screen, player_names)
            save_database(answered_questions, player_names,
                          scores, daily_doubles)

        draw_window_grid_and_refresh(
            screen, questions, selected_question, answered_questions,
            make_player_scores(player_names, scores) )

def run_question(
    screen, category, question, answer, is_dd, question_score,
    selected_question, answered_questions, player_names, scores,
    daily_doubles, answer_server):

    answer_server.current_answer = answer

    if is_dd:
        draw_daily_double_splash(screen, player_names, scores)
        pick_player = pick_dd_player(screen, player_names)
        if pick_player == None:
            return False
        else:
            draw_daily_double_splash(
                screen,
                (player_names[pick_player],),
                (scores[pick_player],) )
            how_much = input_dd_player_wager(
                screen,
                MIN_DAILY_DOUBLE_WAGER,
                max(scores[pick_player], MAX_DAILY_DOUBLE_FOR_NEG) )

    pre_question = ( question if not SHOW_CATEGORY
                     else "%s for %s" % (category,
                                         question_score if not is_dd
                                         else how_much
                                         )
                     )

    draw_window_question_prompts_and_refresh(
        screen, pre_question,
        player_names, NOBODY_BUZZED,
        state=QUESTION_PRE_BUZZ_EXIT)

    while True:
        event = screen.getch()

        if event == ord('s'):
            if is_dd:
                draw_window_question_prompts_and_refresh(
                    screen, question, player_names, pick_player,
                    QUESTION_WAIT_ANSWER)
                correct = run_wait_for_right_wrong(screen)
                scores[pick_player] += (
                    how_much if correct
                    else -how_much )
                if correct:
                    draw_window_question_prompts_and_refresh(
                        screen, answer, player_names, pick_player,
                        QUESTION_ANSWERED_RIGHT)
                else:
                    draw_window_question_prompts_and_refresh(
                        screen, question, player_names, pick_player,
                        QUESTION_EVERYBODY_WRONG)
                    run_until_space(screen)
                    draw_window_question_prompts_and_refresh(
                        screen, answer, player_names, pick_player,
                        QUESTION_EVERYBODY_WRONG)
                # wait for space after showing the answer as is the case
                # in both if and else above
                run_until_space(screen)

            else:
                run_buzzin_attempts(screen, question, answer, question_score,
                                    answered_questions, player_names, scores,
                                    daily_doubles)
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

        answered_questions, player_names, scores, daily_doubles = \
            load_database(questions)

        run_questions_menu(screen, questions, answered_questions, player_names,
                           scores, daily_doubles, answer_server)
        screen.clear()
    finally:
        answer_server.shutdown()

# get the buzzed in player name
def run_buzzin_attempts(
    screen, question, answer, question_score,
    answered_questions, player_names, scores, daily_doubles):
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
                    scores, daily_doubles, question_score)
                state = QUESTION_ANSWERED_RIGHT
                audio.correct()
            else:
                adjust_score_and_save(
                    buzzed_in_player_id, answered_questions, player_names,
                    scores, daily_doubles, -question_score)
                # if all the players have had a chance
                if len(players_allowed) == 1:
                    audio.everybody_wrong()
                    state = QUESTION_EVERYBODY_WRONG
                else:
                    audio.wrong()
                    state = QUESTION_BUZZ_OPEN_AFTER_WRONG

        if previous_state != state:
            state_start_time = time.time()

    # state is one of these two,
    # this approach is a a little more defensive against future changes
    # vs just testing == QUESTION_ANSWERED_WRONG outright
    if state != QUESTION_ANSWERED_RIGHT:
        assert(state == QUESTION_EVERYBODY_WRONG)
        draw_window_question_prompts_and_refresh(
            screen, question, player_names, buzzed_in_player_id, state=state )
        run_until_space(screen)

    draw_window_question_prompts_and_refresh(
        screen, answer, player_names, buzzed_in_player_id, state=state )
    run_until_space(screen)

def run_until_space(screen):
    #First flush the buffer that accumulated while waiting for buzzers
    curses.flushinp()
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

def generate_daily_double_positions(questions):
    num_cat = len(questions)
    assert(NUM_DAILY_DOUBLES <= num_cat)

    # based on http://j-archive.com/ddstats.php?season=26
    # but with some minimal probability of row 1 being a daily double added in
    DAILY_DOUBLE_ROW_STATISTIC = [1, 53, 119, 170, 109]
    daily_double_distrib = []
    num_rows = len(questions[0]["questions"])
    for i, stat in enumerate(DAILY_DOUBLE_ROW_STATISTIC):
        if i == num_rows:
            break
        daily_double_distrib.extend( (i,) * stat )

    # if we have more rows than our statistical table
    if num_rows > len(DAILY_DOUBLE_ROW_STATISTIC):
        # use the last statistic and add all remaining rows in that
        # many times.
        # Multiplying a tuple by a constant int is fun!
        # As is correctly making the arguments to range
        daily_double_distrib.extend(
            tuple(range(
                    len(DAILY_DOUBLE_ROW_STATISTIC),
                    len(DAILY_DOUBLE_ROW_STATISTIC) +
                    num_rows - len(DAILY_DOUBLE_ROW_STATISTIC),
                    ) )
            * DAILY_DOUBLE_ROW_STATISTIC[-1] # last statistic
            )

    # we sample NUM_DAILY_DOUBLES of the categories because there
    # can be at most 1 daily double per category, and in each case
    # chose the row from the row distribution table
    return [ (cat, choice(daily_double_distrib))
        for cat in sample(range(num_cat), NUM_DAILY_DOUBLES)
        ]

def load_database(questions):
    if not exists(PERSIST_FILE):
        attempted_questions = set()
        with open('buzzin') as f:
            player_names = list(player_name.strip() for player_name in f )
        #TODO: Combine names and scores into one datastructure
        scores = [0,] * len(player_names)
        daily_doubles = generate_daily_double_positions(questions)
        save_database(attempted_questions, player_names, scores, daily_doubles)
    else:
        with open(PERSIST_FILE) as f:
            attempted_questions, player_names, scores, daily_doubles = load(f)

    return attempted_questions, player_names, scores, daily_doubles

def adjust_score_and_save(player_id, attempted_questions, player_names,
                          scores, daily_doubles, adj):
    scores[player_id] += adj
    save_database(attempted_questions, player_names, scores, daily_doubles)

def save_database(attempted_questions, player_names, scores, daily_doubles):
    with open(PERSIST_FILE, 'w') as f:
        dump( (attempted_questions, player_names, scores, daily_doubles), f )

if __name__=='__main__':
    curses.wrapper(main)
