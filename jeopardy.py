#!/usr/bin/env python

import curses, json, math
from curses import wrapper

selected_question = [0, 100]
answered_questions = []
max_question = 100
max_category = 0
in_question = False

questions_file = 'practice.json'
questions = []

# main game loop
def main(screen):
	screen.keypad(1)
	
	# initialize colours
	init_colors()
	# initialize questions
	map_questions()
	# initialize selected question bounds
	max_question = int(len(questions[0]["questions"]) * 100)
	max_category = len(questions) - 1
	in_question = False

	# draw window decorations
	draw_window(screen)
	# inialial draw grid
	draw_grid(screen)

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
				in_question = False
			else:
				in_question = True
		
		draw_window(screen)
		if in_question:
			draw_question(screen)
		else:
			draw_grid(screen)
		screen.refresh()

# initialize colour pairs that will be used in app
def init_colors():
	curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
	curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
	curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
	curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_GREEN)

# draws window decorations
def draw_window(screen):
	height, width = screen.getmaxyx()

	# draw app title
	screen.addstr("SkullSpace:: Hacker Jeopardy", curses.color_pair(1))

	# create divider the same width as screen
	line = ""
	while len(line) < width:
		line += "="

	screen.addstr(1, 0, line, curses.color_pair(3))
	screen.addstr(height-2, 0, line, curses.color_pair(3))

	# draw exit instructions	
	screen.addstr(height-1, width-8,"exit: q", curses.color_pair(2))

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

	# print out each category
	pos = 1
	i = 0
	while i < columns:
		screen.addstr(3, pos, fill, curses.color_pair(1))
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

		screen.addstr(4, pos, title, curses.color_pair(1))
		screen.addstr(5, pos, fill, curses.color_pair(1))

		# print question values
		space = ""
		while len(space) < int(math.floor((category_width-4)/2)):
			space += " "

		ypos = 7
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

	while pos < box_height:
		if pos == halfway:
			screen.addstr(pos, 2, question, curses.color_pair(1))
		else:
			screen.addstr(pos, 2, fill, curses.color_pair(1))
		pos += 1

	answered_questions.append([selected_question[0],selected_question[1]])

# load questions from json
def map_questions():
	questions_json = open(questions_file)
	with questions_json as f:
		categories = json.load(f)
		
	for category in categories:
		questions.append(category)
	questions_json.close()

if __name__=='__main__':
	curses.wrapper(main)
