#!/usr/bin/env python

import curses, json, math, sys
from curses import wrapper

from wait_4_buzz import wait_4_buzz

selected_question = [0, 100]
answered_questions = []
max_question = 100
max_category = 0
in_question = False
correct_answer = False
incorrect_answer = False
buzzed_in_player = ""

NOBODY_BUZZED = -1

questions_file = 'questions.json'
questions = []

with open('buzzin') as f:
    player_names = tuple( player_name.strip()
                          for player_name in f )

def run_questions_menu(screen):
    # initialize selected question bounds
    max_question = int(len(questions[0]["questions"]) * 100)
    max_category = len(questions) - 1
    global in_question
    global correct_answer
    global incorrect_answer
    global buzzable

    while True:
        event = screen.getch()
        screen.clear()

        if event == ord("q"):
            break
        elif event == curses.KEY_UP:
            screen.clear()
            if selected_question[1] > 100 and not in_question:
                selected_question[1] -= 100
        elif event == curses.KEY_DOWN:
            screen.clear()
            if selected_question[1] < max_question and not in_question:
                selected_question[1] += 100
        elif event == curses.KEY_RIGHT:
            screen.clear()
            if selected_question[0] < max_category and not in_question:
                selected_question[0] += 1
        elif event == curses.KEY_LEFT:
            screen.clear()
            if selected_question[0] > 0 and not in_question:
                selected_question[0] -= 1
        elif event == ord(" "):
            screen.clear()
            if in_question:
                correct_answer = False
                incorrect_answer = False
                in_question = False
            else:
                in_question = True
        elif event == ord('r') and in_question:
            correct_answer = True
            incorrect_answer = False
        elif event == ord('w') and in_question:
            incorrect_answer = True
            correct_answer = False
        elif event == ord('s') and in_question:
            incorrect_answer = False
            correct_answer = False
            check_buzzin()

        draw_window(screen)
        if in_question:
            draw_question(screen)
        else:
            draw_grid(screen)
        screen.refresh()    

# main game loop
def main(screen):
    screen.keypad(1)
    
    # initialize colours
    init_colors()
    # initialize questions
    map_questions()

    draw_splash(screen)
    screen.getch()
    screen.clear()    
    
    draw_window(screen) # draw window decorations
    draw_grid(screen) # initial draw grid
    screen.refresh()

    run_questions_menu(screen)

# initialize colour pairs that will be used in app
def init_colors():
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_GREEN)
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_YELLOW)

def draw_splash(screen):
    with open('splash_ascii_art.txt') as f:
        splash_ascii_art = tuple(
            line[:-1] # remove newline character from each line
            for line in f)

    height, width = screen.getmaxyx()

    # add each line of art to the screen, starting from row 1 and column 2
    for i,file_line in enumerate(splash_ascii_art,1):
        screen.addstr(i,2, file_line, curses.color_pair(1) )

    # create divider the same width as screen
    screen.addstr(height-3, 0, "=" * width, curses.color_pair(3))

    # draw any key instructions right justified (so starting at width-len)
    any_key_msg = " press any key to continue "
    screen.addstr(height-2, width-len(any_key_msg)-2,
                  any_key_msg, curses.color_pair(2))

# draws window decorations
def draw_window(screen):
    height, width = screen.getmaxyx()

    # create divider the same width as screen
    line = ""
    spacer = ""
    while len(line) < width:
        line += "="
        spacer += " "

    title = " Hacker Jeopardy"
    while len(title) < width:
        title += " "

    # draw app title
    screen.addstr(spacer, curses.color_pair(1))
    screen.addstr(1, 0, title, curses.color_pair(1))
    screen.addstr(2, 0, spacer, curses.color_pair(1))

    screen.addstr(3, 0, line, curses.color_pair(3))
    screen.addstr(height-3, 0, line, curses.color_pair(3))

    # draw response actions
    screen.addstr(height-2, 2, " correct answer: r ", curses.color_pair(4))
    screen.addstr(height-2, 22, " incorrect answer: w ", curses.color_pair(5))
    screen.addstr(height-2, 44, " allow buzz in: s ", curses.color_pair(1))
    # draw exit instructions    
    screen.addstr(height-2, width-11, " exit: q ", curses.color_pair(2))

# draw question grid on screen
def draw_grid(screen):
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

    # i = 0
    # lns = 1
    # while i < columns:
    #   if len(questions[i]["name"]):
    #   # check if the questions is wider than the screen   

    # print out each category
    pos = 1
    i = 0
    while i < columns:
        screen.addstr(5, pos, fill, curses.color_pair(1))
        category_length = len(questions[i]["name"])
        dif = category_width - category_length
        title = questions[i]["name"]
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
            elif [i, int(j*100)] in answered_questions:
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

# draws the selected question on the screen
def draw_question(screen):
    height, width = screen.getmaxyx()

    fill = ""
    while len(fill) < width - 4:
        fill += " "

    box_height = height - 6
    halfway = math.floor((height-3)/2)
    pos = 4

    question = questions[selected_question[0]]["questions"][int(selected_question[1]/100-1)]["question"]
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
            screen.addstr(pos, 2, question, bkg_color)
        else:
            screen.addstr(pos, 2, fill, bkg_color)
        pos += 1
    if len(buzzed_in_player) > 0:
        player = buzzed_in_player
        while len(player) < width-4:
            player = " " + player + " "
        if len(player) > width-4:
            player = player[:-1]
        screen.addstr(pos, 2, player, curses.color_pair(4))

    answered_questions.append([selected_question[0],selected_question[1]])

# get the buzzed in player name
def check_buzzin():
    global buzzed_in_player
    buzzed_in_player_id = wait_4_buzz()

    if buzzed_in_player_id != NOBODY_BUZZED:
        buzzed_in_player = player_names[buzzed_in_player_id]
    else:
        # need to do something here
        raise Exception("Nobody buzzed not yet implemented!")

# load questions from json
def map_questions():
    global questions
    questions_json = open(questions_file)
    with questions_json as f:
        questions = json.load(f)

if __name__=='__main__':
    curses.wrapper(main)
