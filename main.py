import asyncio
import time
import curses
from random import randint, choice


TIC_TIMEOUT = 0.1


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


def draw(canvas):
    canvas.border()
    rows, columns = canvas.getmaxyx()
    max_height, max_width = rows - 2, columns - 2
    curses.curs_set(False)
    star_coordinates = [
        (randint(1, max_height), randint(1, max_width))
        for _ in range(100)
    ]
    star_symbols = '+*:.'
    coroutines = [
        blink(canvas, coordinate[0], coordinate[1], choice(star_symbols))
        for coordinate in star_coordinates
    ]
    coroutines.append(fire(canvas, 15, 50))
    while True:
        for coroutine in coroutines:
            coroutine.send(None)
            canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
