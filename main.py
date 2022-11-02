import asyncio
import time
import curses
from random import randint, choice
from itertools import cycle


TIC_TIMEOUT = 0.1
SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258


def read_frame_file(file_name):
    """Read frame file"""

    with open(f'frames/{file_name}', 'r') as frame_file:
        frame = frame_file.read()
    return frame


def draw_frame(canvas, start_row, start_column, text, negative=False):
    """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position is not in a lower right corner
            # of the window.
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


async def blink(canvas, row, column, symbol='*'):
    """Display animation of blinking star, position and symbol can be specified."""

    offset_time = randint(3, 12)

    while True:
        for _ in range(20):
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await asyncio.sleep(0)
        for _ in range(3 + offset_time):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)
        for _ in range(5):
            canvas.addstr(row, column, symbol, curses.A_BOLD)
            await asyncio.sleep(0)
        for _ in range(3):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def display_rocket(canvas, rocket_frames, raw, column):
    for frame in cycle(rocket_frames):
        draw_frame(canvas, raw, column, frame)
        await asyncio.sleep(0)
        raw_direction, column_direction, _ = read_controls(canvas)
        next_raw = raw + raw_direction
        next_column = column + column_direction
        await asyncio.sleep(0)
        raw_direction, column_direction, _ = read_controls(canvas)
        next_raw += raw_direction
        next_column += column_direction
        draw_frame(canvas, raw, column, frame, negative=True)
        raw, column = next_raw, next_column


def draw(canvas):
    canvas.border()
    rows, columns = canvas.getmaxyx()
    max_height, max_width = rows - 2, columns - 2
    curses.curs_set(False)
    canvas.nodelay(True)
    rocket_frame_1 = read_frame_file('rocket_frame_1.txt')
    rocket_frame_2 = read_frame_file('rocket_frame_2.txt')
    rocket_frames = [rocket_frame_1, rocket_frame_2]
    star_coordinates = [
        (randint(1, max_height), randint(1, max_width))
        for _ in range(100)
    ]
    star_symbols = '+*:.'
    coroutines = [
        blink(canvas, coordinate[0], coordinate[1], choice(star_symbols))
        for coordinate in star_coordinates
    ]
    coroutines.append(display_rocket(canvas, rocket_frames, 20, 20))
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
