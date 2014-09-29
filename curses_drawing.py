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

SPLASH_TEXT = "Hacker Jeopardy!!!"

def draw_window_grid_and_refresh(
    screen, questions, selected_question, answered_questions, player_scores):
    screen.clear()

    draw_grid(
        screen, questions,
        selected_question, answered_questions,
        player_scores )
    height, width = screen.getmaxyx()

    screen.addstr(height-2, 2, " edit scores: e ", curses.color_pair(2) )

    # draw exit instructions    
    exit_instructions = " exit: q "
    screen.addstr(height-2, width-len(exit_instructions)-2,
                  exit_instructions, curses.color_pair(2))

    screen.refresh()

def waiting_for_buzz_prompt(screen, height):
    screen.addstr(height-2, 2, " waiting for buzz ", curses.color_pair(1))

def prompt_buzz_enable(screen, height):
    screen.addstr(height-2, 2, " allow buzz in: s ", curses.color_pair(1))

def prompt_right_answer(screen, height):
    correct_answer_prompt = " correct answer: r "
    screen.addstr(height-2, 2, correct_answer_prompt, curses.color_pair(4))
    screen.addstr(height-2, 2 + len(correct_answer_prompt),
                  " incorrect answer: w ", curses.color_pair(5))

def draw_window_question_prompts_and_refresh(
    screen, prompts_func,
    correct_answer, incorrect_answer,
    question, player_name=""):
    screen.clear()

    height, width = screen.getmaxyx()
    # draw response actions
    prompts_func(screen, height)

    draw_question(screen, correct_answer, incorrect_answer,
                  question, player_name)
    screen.refresh()

# initialize colour pairs that will be used in app
def init_colors():
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_GREEN)
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_YELLOW)

def text_in_screen_center(screen, text, horiz_border=5, vert_border=5,
                          color=3):
    height, width = screen.getmaxyx()
    allowable_width = width - horiz_border*2
    output_lines = wrap(text, width=allowable_width)
    assert( len(output_lines) + vert_border*2 <= height )
    start_line = vert_border + (height-vert_border*2)//2
    for i, line_txt in enumerate(output_lines, start_line):
        left_start = horiz_border+1
        if len(line_txt) < allowable_width:
            center = allowable_width // 2
            half_txt = len(line_txt) // 2
            left_start += center - half_txt
        screen.addstr(i, left_start, line_txt, curses.color_pair(color) )

def draw_splash(screen):
    text_in_screen_center(screen, SPLASH_TEXT, color=1)
    height, width = screen.getmaxyx()

    # create divider the same width as screen
    screen.addstr(height-3, 0, "=" * width, curses.color_pair(3))

    # draw any key instructions right justified (so starting at width-len)
    any_key_msg = " press any key to continue "
    screen.addstr(height-2, width-len(any_key_msg)-2,
                  any_key_msg, curses.color_pair(2))

# draw question grid on screen
def draw_grid(
    screen, questions,
    selected_question, answered_questions,
    player_scores ):
    height, width = screen.getmaxyx()

    columns = len(questions)
    rows = len(questions[0]["questions"])

    # 4 is the num of line used for window decorations
    category_height = int(math.floor(height/rows))-4
    # columns *2 allows 1 row space on each side of category
    category_width = int(math.floor((width-(columns*2))/columns))

    # border for categories 
    fill = ""
    empty = ""
    while len(fill) < category_width:
        fill += "*"
        empty += " "

    # print out each category
    pos = 1
    i = 0
    while i < columns:
        screen.addstr(5, pos, fill, curses.color_pair(1))
        category_length = len(questions[i]["abrev_name"])
        dif = category_width - category_length
        title = questions[i]["abrev_name"]
        if dif > 0:
            if dif % 2 == 0:
                while len(title) < category_width:
                    title = " " + title + " "
            else:
                title = " " + title
                while len(title) < category_width:
                    title = " " + title + " "
        else:
            title = title

        screen.addstr(6, pos, title, curses.color_pair(1))
        screen.addstr(7, pos, fill, curses.color_pair(1))

        # print question values
        space = ""
        while len(space) < int(math.floor((category_width-4)/2)):
            space += " "

        ypos = 9
        j = 1
        while j <= rows:
            cur_color = curses.color_pair(1)
            if i == selected_question[0] and j*100 == selected_question[1]:
                cur_color = curses.color_pair(4)
            elif (i, int(j*100)) in answered_questions:
                cur_color = curses.color_pair(2)

            screen.addstr(ypos, pos, empty, cur_color)
            ypos += 1
            level = space + str(j) + "00 " + space
            screen.addstr(ypos, pos, level, cur_color)
            ypos += 1
            screen.addstr(ypos, pos, empty, cur_color)
            ypos += 2
            j += 1

        pos += category_width + 2
        i += 1

    for a, player_score in enumerate(player_scores):
        screen.addstr(ypos+2+a, 20, player_score, curses.color_pair(3) )

# draws the selected question on the screen
def draw_question(screen, correct_answer, incorrect_answer,
                  question, player_name):
    height, width = screen.getmaxyx()

    fill = ""
    while len(fill) < width - 4:
        fill += " "

    box_height = height - 6
    halfway = math.floor((height-3)/2)
    pos = 4

    original_question = question

    dif = width - 4 - len(question)
    if dif > 0:
        if dif % 2 == 0:
            while len(question) < width - 4:
                question = " " + question + " "
        else:
            question = question + " "
            while len(question) < width - 4:
                question = " " + question + " "
    # default colour to blue
    bkg_color = curses.color_pair(1)
    if correct_answer:
        # if answer is correct, switch to green colour
        bkg_color = curses.color_pair(4)
    elif incorrect_answer:
        # if answer is incorrect, switch to red colour
        bkg_color = curses.color_pair(2)

    while pos < box_height:
        if pos == halfway:
            # for large multi-line questions
            if len(original_question) +20 > width:
                question_lines = wrap(original_question, width-20)
                for a, question_line in enumerate(question_lines):
                    screen.addstr(pos+a, 2, center(question_line,width-4),
                                  bkg_color)
                pos += len(question_lines)-1
            else:
                screen.addstr(pos, 2, question, bkg_color)
        else:
            screen.addstr(pos, 2, fill, bkg_color)
        pos += 1
    if len(player_name) > 0:
        while len(player_name) < width-4:
            player_name = " " + player_name + " "
        if len(player_name) > width-4:
            player_name = player_name[:-1]
        screen.addstr(pos, 2, player_name, curses.color_pair(4))
