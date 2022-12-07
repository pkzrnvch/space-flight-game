import asyncio
import curses
import time
from itertools import cycle
from random import randint, choice

from physics import update_speed
from obstacles import Obstacle
from explosion import explode
from curses_tools import draw_frame, get_frame_size, read_controls
from game_scenario import PHRASES, get_garbage_delay_tics


TIC_TIMEOUT = 0.1
STARS_AMOUNT = 100


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, offset_tics, symbol='*'):
    """Display animation of blinking star, position and symbol can be specified."""

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20 + offset_tics)
        canvas.addstr(row, column, symbol)
        await sleep(3)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)
        canvas.addstr(row, column, symbol)
        await sleep(3)


async def fire(canvas, start_row, start_column, rows_speed=-0.5, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep()

    canvas.addstr(round(row), round(column), 'O')
    await sleep()
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                return
        canvas.addstr(round(row), round(column), symbol)
        await sleep()
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def display_rocket(canvas, rocket_frames, max_speed=3):
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

    row_speed = column_speed = 0

    for frame in cycle(rocket_frames):
        row_direction, column_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(
            row_speed,
            column_speed,
            row_direction,
            column_direction,
            row_speed_limit=max_speed,
            column_speed_limit=max_speed
        )

        row += row_speed
        column += column_speed
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
        if space_pressed and current_year >= 2020:
            coroutines.append(fire(canvas, row, column + int(frame_width / 2)))
        draw_frame(canvas, row, column, frame)
        await sleep()
        draw_frame(canvas, row, column, frame, negative=True)

        for obstacle in obstacles:
            if obstacle.has_collision(row, column + int(frame_width / 2)):
                global game_over
                game_over = True
                coroutines.append(show_gameover(canvas))
                return


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""

    rows_number, columns_number = canvas.getmaxyx()

    row = 1

    frame_rows_number, frame_columns_number = get_frame_size(garbage_frame)

    while row < rows_number:
        try:
            obstacle = Obstacle(
                row,
                column,
                frame_rows_number,
                frame_columns_number
            )
            obstacles.append(obstacle)
            draw_frame(canvas, row, column, garbage_frame)
            await sleep()
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            row += speed

            frame_center_row = int(row + frame_rows_number / 2)
            frame_center_column = int(column + frame_columns_number / 2)

            if obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(obstacle)
                coroutines.append(
                    explode(canvas, frame_center_row, frame_center_column)
                )
                return
            if game_over:
                return
        finally:
            obstacles.remove(obstacle)


async def fill_orbit_with_garbage(canvas, garbage_frames, max_column_within_borders):
    while not game_over:
        garbage_delay_tics = get_garbage_delay_tics(current_year)
        frame = choice(garbage_frames)
        _, frame_columns_number = get_frame_size(frame)
        if garbage_delay_tics:
            coroutines.append(
                fly_garbage(
                    canvas,
                    column=randint(
                        1,
                        max_column_within_borders - frame_columns_number
                    ),
                    garbage_frame=frame,
                )
            )
            await sleep(garbage_delay_tics)
        else:
            await sleep(1)


async def show_gameover(canvas):
    rows_number, columns_number = canvas.getmaxyx()
    max_row, max_column = rows_number - 1, columns_number - 1
    max_row_within_borders = max_row - 1
    max_column_within_borders = max_column - 1
    with open('frames/gameover_frame.txt', 'r') as frame_file:
        game_over_frame = frame_file.read()
    frame_rows_number, frame_columns_number = get_frame_size(game_over_frame)
    frame_position_row = int(
        max_row_within_borders / 2 - frame_rows_number / 2
    )
    frame_position_column = int(
        max_column_within_borders / 2 - frame_columns_number / 2
    )
    while True:
        draw_frame(
            canvas,
            frame_position_row,
            frame_position_column,
            game_over_frame
        )

        await sleep()

        draw_frame(
            canvas,
            frame_position_row,
            frame_position_column,
            game_over_frame,
            negative=True
        )


async def pass_years():
    global current_year
    while not game_over:
        await sleep(15)
        current_year += 1


async def draw_year(canvas):
    rows_number, columns_number = canvas.getmaxyx()
    year_window_rows = 4
    year_window_columns = 50
    year_window = canvas.derwin(
        year_window_rows,
        year_window_columns,
        rows_number - year_window_rows - 1,
        columns_number - year_window_columns - 1
    )
    while not game_over:
        phrase = PHRASES.get(current_year)
        if phrase:
            frame = f'{current_year} - {phrase}'
        else:
            frame = str(current_year)
        frame_rows_number, frame_columns_number = get_frame_size(frame)
        frame_position_row = int(
            year_window_rows / 2 - frame_rows_number / 2
        )
        frame_position_column = int(
            year_window_columns / 2 - frame_columns_number / 2
        )
        year_window.border()
        draw_frame(
            year_window,
            frame_position_row,
            frame_position_column,
            frame)
        await sleep()
        draw_frame(
            year_window,
            frame_position_row,
            frame_position_column,
            frame,
            negative=True
        )


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

    garbage_frame_files = [
        'duck.txt',
        'hubble.txt',
        'lamp.txt',
        'trash_large.txt',
        'trash_small.txt',
        'trash_xl.txt'
    ]

    rocket_frames = []
    for file in rocket_frame_files:
        with open(f'frames/rocket_frames/{file}', 'r') as frame_file:
            frame = frame_file.read()
            rocket_frames.append(frame)
            rocket_frames.append(frame)

    garbage_frames = []
    for file in garbage_frame_files:
        with open(f'frames/garbage_frames/{file}', 'r') as frame_file:
            frame = frame_file.read()
            garbage_frames.append(frame)
            garbage_frames.append(frame)

    star_coordinates = [(
        randint(min_row_within_borders, max_row_within_borders),
        randint(min_column_within_borders, max_column_within_borders)
    ) for _ in range(STARS_AMOUNT)]
    star_symbols = '+*:.'

    coroutines.extend(
        [blink(
            canvas,
            coordinate[0],
            coordinate[1],
            randint(3, 12),
            choice(star_symbols)
        ) for coordinate in star_coordinates]
    )

    coroutines.append(
        display_rocket(canvas, rocket_frames)
    )

    coroutines.append(
        fill_orbit_with_garbage(
            canvas,
            garbage_frames,
            max_column_within_borders
        )
    )

    coroutines.append(draw_year(canvas))
    coroutines.append(pass_years())

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        canvas.border()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    coroutines = []
    obstacles = []
    obstacles_in_last_collisions = []
    current_year = 1957
    game_over = False
    curses.update_lines_cols()
    curses.wrapper(draw)
