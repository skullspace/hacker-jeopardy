#!/usr/bin/env python

import curses, json, math
from curses import wrapper

questions_file = 'practice.json'
questions = []

# main game loop
def main(screen):
	screen.keypad(1)
	
	# initialize colours
	init_colors()
	# initialize questions
	map_questions()

	# draw window decorations
	draw_window(screen)

	while True:
		event = screen.getch()
		screen.clear()

		if event == ord("q"):
			break
		elif event == curses.KEY_UP:
			screen.clear()
		elif event == curses.KEY_DOWN:
			screen.clear()
		
		draw_window(screen)
		draw_grid(screen)
		screen.refresh()

# initialize colour pairs that will be used in app
def init_colors():
	curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
	curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
	curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)

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
			screen.addstr(ypos, pos, empty, curses.color_pair(1))
			ypos += 1
			level = space + str(j) + "00 " + space
			screen.addstr(ypos, pos, level, curses.color_pair(1))
			ypos += 1
			screen.addstr(ypos, pos, empty, curses.color_pair(1))
			ypos += 2
			j += 1

		pos += category_width + 2
		i += 1

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
