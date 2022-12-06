import asyncio
import curses
import time
from itertools import cycle
from random import randint, choice

TIC_TIMEOUT = 0.1
SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258


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


def get_frame_size(text):
    """Calculate size of multiline text fragment, return pair — number of rows and columns."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


def read_controls(canvas):
    """Read keys pressed and returns tuple with controls state."""

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


async def blink(canvas, row, column, offset_tics, symbol='*'):
    """Display animation of blinking star, position and symbol can be specified."""

    while True:
        for _ in range(20):
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await asyncio.sleep(0)
        for _ in range(3 + offset_tics):
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


async def display_rocket(canvas, rocket_frames):
    """Display rocket movement animation."""

    # window.getmaxyx() actually returns total number of rows and columns:
    rows_number, columns_number = canvas.getmaxyx()

    # Since row and column numeration starts at zero:
    max_row, max_column = rows_number - 1, columns_number - 1

    # Since we want stars to be displayed in the area within borders:
    max_row_within_borders = max_row - 1
    max_column_within_borders = max_column - 1
    min_row_within_borders = min_column_within_borders = 1

    frame_height, frame_width = get_frame_size(rocket_frames[0])
    row = round(rows_number / 2 - frame_height / 2)
    column = round(columns_number / 2 - frame_width / 2)

    for frame in cycle(rocket_frames):
        row_direction, column_direction, _ = read_controls(canvas)
        row += row_direction
        column += column_direction
        if row >= min_row_within_borders:
            row = min(
                max_row_within_borders - frame_height + 1,
                row
            )
        else:
            row = min_row_within_borders
        if column >= min_column_within_borders:
            column = min(
                max_column_within_borders - frame_width + 1,
                column
            )
        else:
            column = min_column_within_borders
        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed


def draw(canvas):
    canvas.border()

    # window.getmaxyx() actually returns total number of rows and columns:
    rows_number, columns_number = canvas.getmaxyx()

    # Since row and column numeration starts at zero:
    max_row, max_column = rows_number - 1, columns_number - 1

    # Since we want stars to be displayed in the area within borders:
    max_row_within_borders = max_row - 1
    max_column_within_borders = max_column - 1
    min_row_within_borders = min_column_within_borders = 1

    curses.curs_set(False)
    canvas.nodelay(True)

    rocket_frame_files = [
        'rocket_frame_1.txt',
        'rocket_frame_2.txt'
    ]
    rocket_frames = []
    for file in rocket_frame_files:
        with open(f'frames/rocket_frames/{file}', 'r') as frame_file:
            frame = frame_file.read()
            rocket_frames.append(frame)
            rocket_frames.append(frame)

    star_coordinates = [(
        randint(min_row_within_borders, max_row_within_borders),
        randint(min_column_within_borders, max_column_within_borders)
    ) for _ in range(100)]
    star_symbols = '+*:.'

    coroutines = [
        blink(
            canvas,
            coordinate[0],
            coordinate[1],
            randint(3, 12),
            choice(star_symbols)
        ) for coordinate in star_coordinates
    ]
    coroutines.append(display_rocket(canvas, rocket_frames))

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
