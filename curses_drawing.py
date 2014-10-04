# Copyright Skullspace, 2014
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved. This file is offered as-is,
# without any warranty.
# http://www.gnu.org/prep/maintain/html_node/License-Notices-for-Other-Files.html
# @author Jeremy Hiebert <jkhiebert@gmail.com>
# @author Mark Jenkins <mark@markjenkins.ca>

import curses, math
from textwrap import wrap
from string import center

from question_states import *

SPLASH_TEXT = "Hacker Jeopardy!!!"
SPLASH_ANY_KEY_MSG = " any key to continue"

# has to be greater than 1
BOT_INSTRUCT_OFFSET = 1

GRID_HORIZ_BORDER = 0
GRID_VERT_OFFSET = 0
INNER_GRID_BORDER = 1
VERT_INNER_GRID_BORDER = 0
SPACE_FROM_CATEGORY_TO_LEVELS = 1
SPACE_BETWEEN_LEVELS = 1

SPLASH_HORIZON_BORDER = 1
SPLASH_VERT_BORDER = 0

SPLASH_DIVIDER_OFFSET = 2
SPLASH_BOT_INSTRUCT_OFFSET = 1

SCORE_INSTRUCT_OFFSET = 0
EXIT_INSTRUCT_OFFSET = 1
assert(EXIT_INSTRUCT_OFFSET >= 1 )

QUESTION_BOX_HORIZ_BORDER = 0
QUESTION_BOX_TOP_OFFSET = 0
QUESTION_BOX_BOTTOM_OFFSET = 2
QUESTION_TXT_VERT_BORDER = 0
QUESTION_TXT_HORIZ_BORDER = 0
PLAYER_NAME_BOTTOM_OFFSET = 2

EXIT_INSTRUCT = "exit: q"
EDIT_SCORE_INSTRUCT = "edit scores: e"

GRID_PLAYER_SCORES_HORIZ_OFFSET = 0

PLAYER_SEP_CHARS = " "

POINTS = tuple( range(100, 500+1, 100) )

(COLOUR_PAIR_GOOD_FEEL,
 COLOUR_PAIR_BAD_FEEL,
 COLOUR_PAIR_MAX_CONTRAST,
 COLOUR_PAIR_REALLY_GOOD,
 COLOUR_PAIR_MEH
 ) = tuple(range(1, 5+1))

def draw_window_grid_and_refresh(
    screen, questions, selected_question, answered_questions, player_scores):
    screen.clear()

    draw_grid(
        screen, questions,
        selected_question, answered_questions,
        player_scores )
    height, width = screen.getmaxyx()

    screen.addstr(height-BOT_INSTRUCT_OFFSET,
                  SCORE_INSTRUCT_OFFSET,
                  EDIT_SCORE_INSTRUCT,
                  CURSES_COLOUR_PAIR_BAD_FEEL )

    # draw exit instructions    
    exit_instructions = EXIT_INSTRUCT
    screen.addstr(height-BOT_INSTRUCT_OFFSET,
                  width-len(exit_instructions)-EXIT_INSTRUCT_OFFSET,
                  exit_instructions, CURSES_COLOUR_PAIR_BAD_FEEL)

    screen.refresh()

# initialize colour pairs that will be used in app
def init_colors():
    for i, background in enumerate( (
        curses.COLOR_BLUE, # COLOUR_PAIR_GOOD_FEEL
        curses.COLOR_RED, # COLOUR_PAIR_BAD_FEEL,
        curses.COLOR_BLACK, # COLOUR_PAIR_MAX_CONTRAST
        curses.COLOR_GREEN, # COLOUR_PAIR_REALLY_GOOD,
        curses.COLOR_YELLOW, # COLOUR_PAIR_MEH
        ), 1 ):
        curses.init_pair(i, curses.COLOR_WHITE, background )

    global CURSES_COLOUR_PAIR_GOOD_FEEL
    global CURSES_COLOUR_PAIR_BAD_FEEL
    global CURSES_COLOUR_PAIR_MAX_CONTRAST
    global CURSES_COLOUR_PAIR_REALLY_GOOD
    global CURSES_COLOUR_PAIR_MEH

    (CURSES_COLOUR_PAIR_GOOD_FEEL, CURSES_COLOUR_PAIR_BAD_FEEL,
     CURSES_COLOUR_PAIR_MAX_CONTRAST, CURSES_COLOUR_PAIR_REALLY_GOOD,
     CURSES_COLOUR_PAIR_MEH) = tuple(
        curses.color_pair(pair_code)
        for pair_code in
         (COLOUR_PAIR_GOOD_FEEL,
          COLOUR_PAIR_BAD_FEEL,
          COLOUR_PAIR_MAX_CONTRAST,
          COLOUR_PAIR_REALLY_GOOD,
          COLOUR_PAIR_MEH)
        )

def text_in_screen_center(screen, text, horiz_border=5,
                          vert_top_skip=0, vert_bottom_skip=2,
                          color=COLOUR_PAIR_MAX_CONTRAST):
    height, width = screen.getmaxyx()
    allowable_width = width - horiz_border*2
    output_lines = wrap(text, width=allowable_width)
    allowable_height = height - vert_top_skip - vert_bottom_skip
    output_lines = output_lines[:allowable_height]
    start_line = vert_top_skip + allowable_height//2 - len(output_lines)//2
    for i, line_txt in enumerate(output_lines, start_line):
        screen.addstr(i, horiz_border,
                      center(line_txt, allowable_width, " "),
                      curses.color_pair(color) )

def draw_splash(screen):
    text_in_screen_center(screen, SPLASH_TEXT, color=1,
                          vert_top_skip=SPLASH_VERT_BORDER,
                          vert_bottom_skip=SPLASH_VERT_BORDER,
                          horiz_border=SPLASH_HORIZON_BORDER,
                          )
    height, width = screen.getmaxyx()

    if SPLASH_DIVIDER_OFFSET > SPLASH_BOT_INSTRUCT_OFFSET:
        # create divider the same width as screen
        screen.addstr(
            height-SPLASH_DIVIDER_OFFSET, 0,
            "=" * width, CURSES_COLOUR_PAIR_MAX_CONTRAST)

    # draw any key instructions right justified (so starting at width-len)
    assert(len(SPLASH_ANY_KEY_MSG) <= width)
    if SPLASH_BOT_INSTRUCT_OFFSET >= 1:
        screen.addstr(height-SPLASH_BOT_INSTRUCT_OFFSET,
                      0,
                      SPLASH_ANY_KEY_MSG,
                      CURSES_COLOUR_PAIR_BAD_FEEL)

# draw question grid on screen
def draw_grid(
    screen, questions,
    selected_question, answered_questions,
    player_scores ):
    height, width = screen.getmaxyx()

    columns = len(questions)
    rows = len(questions[0]["questions"])

    # take the total screen width, subtract the border zone,
    # and allow INNER_GRID_BORDER space between each column
    category_width = ( width-GRID_HORIZ_BORDER*2-
                       (columns-1)*INNER_GRID_BORDER ) // columns

    question_grid_start = GRID_VERT_OFFSET + SPACE_FROM_CATEGORY_TO_LEVELS

    for i, category in enumerate(questions):
        category_name = (category["name"]
                         if len(category["name"]) <= category_width
                         else category["abrev_name"]
                         )[:category_width]
        assert( len(category_name) <= category_width )

        horizontal_position = (
            GRID_HORIZ_BORDER + i*category_width +
            i*INNER_GRID_BORDER
            )

        screen.addstr(
            GRID_VERT_OFFSET,
            horizontal_position,
            center(category_name, category_width, " "),
            CURSES_COLOUR_PAIR_GOOD_FEEL
            )

        for j, score in enumerate(POINTS):
            cur_color = CURSES_COLOUR_PAIR_GOOD_FEEL
            if (i, score) == tuple(selected_question):
                cur_color = CURSES_COLOUR_PAIR_REALLY_GOOD
            elif (i, score) in answered_questions:
                cur_color = CURSES_COLOUR_PAIR_BAD_FEEL

            screen.addstr(
                question_grid_start + j+j*VERT_INNER_GRID_BORDER,
                horizontal_position,
                center(str(score), category_width, " "),
                cur_color )
    
    player_scores_str = PLAYER_SEP_CHARS.join(player_scores)
    player_scores_str = \
        player_scores_str[:(width-GRID_PLAYER_SCORES_HORIZ_OFFSET)]
    screen.addstr(height-2, GRID_PLAYER_SCORES_HORIZ_OFFSET,
                  player_scores_str,
                  CURSES_COLOUR_PAIR_MAX_CONTRAST )

# draws the selected question on the screen
def draw_window_question_prompts_and_refresh(
    screen, question, player_name="", state=None):

    screen.clear()

    height, width = screen.getmaxyx()

    msg_stuff = {
        QUESTION_PRE_BUZZ_EXIT:
            (" space to return, s to show ", CURSES_COLOUR_PAIR_GOOD_FEEL),
        QUESTION_PRE_BUZZ: None,
        QUESTION_BUZZ_OPEN:
            (" waiting for buzz ", CURSES_COLOUR_PAIR_GOOD_FEEL),
        QUESTION_WAIT_ANSWER:
            (" correct answer: r ", CURSES_COLOUR_PAIR_REALLY_GOOD,
             " incorrect answer: w ", CURSES_COLOUR_PAIR_MEH, ),
        QUESTION_BUZZ_OPEN_AFTER_WRONG: None,
        QUESTION_ANSWERED_RIGHT: None,
        QUESTION_EVERYBODY_WRONG: None,
        }[state]
    if msg_stuff != None:
        horiz_position = 2
        for msg, msg_color_pair in zip(*[iter(msg_stuff)]*2 ):
            screen.addstr(height-BOT_INSTRUCT_OFFSET,
                          horiz_position, msg, msg_color_pair)
            horiz_position += len(msg)


    fill = " " * (width-QUESTION_BOX_HORIZ_BORDER*2)

    bkg_color = {
        QUESTION_PRE_BUZZ_EXIT: COLOUR_PAIR_GOOD_FEEL,
        QUESTION_PRE_BUZZ: COLOUR_PAIR_MAX_CONTRAST,
        QUESTION_BUZZ_OPEN: COLOUR_PAIR_MEH,
        QUESTION_WAIT_ANSWER: COLOUR_PAIR_GOOD_FEEL,
        QUESTION_BUZZ_OPEN_AFTER_WRONG: COLOUR_PAIR_BAD_FEEL,
        QUESTION_ANSWERED_RIGHT: COLOUR_PAIR_REALLY_GOOD,
        QUESTION_EVERYBODY_WRONG: COLOUR_PAIR_BAD_FEEL,
        }[state]

    # okay, so its a little inefficient to draw all the fill and over
    # draw it with text second. Sue me.
    for i in range(0+QUESTION_BOX_TOP_OFFSET,
                   height - QUESTION_BOX_BOTTOM_OFFSET):
        screen.addstr(
            i, QUESTION_BOX_HORIZ_BORDER,
            fill, curses.color_pair(bkg_color) )
    text_in_screen_center(
        screen, question,
        vert_top_skip=0, vert_bottom_skip=2,
        horiz_border=QUESTION_TXT_HORIZ_BORDER,
        color=bkg_color)

    if len(player_name) > 0:
        player_line = center(player_name,
                             width-QUESTION_BOX_HORIZ_BORDER*2,
                             " ")
        player_line_color = CURSES_COLOUR_PAIR_REALLY_GOOD
    else:
        player_line = " " * (width-QUESTION_BOX_HORIZ_BORDER*2)
        player_line_color = CURSES_COLOUR_PAIR_MAX_CONTRAST
    screen.addstr(
        height-PLAYER_NAME_BOTTOM_OFFSET,
        QUESTION_BOX_HORIZ_BORDER, player_line,
        player_line_color)
            

    screen.refresh()

