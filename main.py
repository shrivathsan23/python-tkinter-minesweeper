import time
import random

from threading import Thread
from collections import deque

from tkinter import Tk, Frame, Label, Button

class State:
    CLOSED_TILE = '#4287F5'
    OPEN_TILE = '#C8D3E6'
    BOMB_TILE = '#C4471A'

class Tile(Label):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config(width = 2, relief = 'raised')
        
        self.init_tile()
    
    def init_tile(self):
        self.is_opened = False
        self.is_flagged = False
        self.value = ''

        self.config(bg = State.CLOSED_TILE, text = self.value)
    
    def get_value(self):
        return self.value
    
    def set_value(self, value):
        self.value = value
    
    def open_tile(self):
        if not self.is_flagged:
            self.is_opened = True
    
    def toggle_flag(self):
        if not self.is_opened:
            self.config(text = '' if self.is_flagged else 'F')
            self.is_flagged = not self.is_flagged
    
    def get_flag(self):
        return self.is_flagged
    
    def reset_tile(self):
        self.init_tile()
    
    def display_value(self):
        if not self.is_flagged:
            self.config(text = self.value, bg = State.OPEN_TILE)
    
    def display_bomb(self):
        self.config(text = self.value, bg = State.BOMB_TILE)
    
    def force_open(self):
        self.is_opened = True
        self.is_flagged = False

        self.display_value()
    
    def is_tile_open(self):
        return self.is_opened
    
    def is_tile_flagged(self):
        return self.is_flagged
        
class Land(Tk):
    def __init__(self, ROWS = 25, COLS = 25):
        super().__init__()

        self.ROWS = ROWS
        self.COLS = COLS

        self.BOMBS_COUNT = (self.ROWS * self.COLS * 15) // 100
        self.WINNING_TILE_COUNT = (self.ROWS * self.COLS) - self.BOMBS_COUNT

        self.ALL_DIRS = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1)
        ]

        self.FOUR_DIRS = [
            (-1, 0),
            (0, -1),
            (0, 1),
            (1, 0)
        ]

        self.title('Minesweeper')
        self.resizable(False, False)

        self.tiles_frame = Frame(self, bg = 'white', relief = 'sunken')
        self.tiles_frame.pack()

        self.tiles = [[None for j in range(self.COLS)] for i in range(self.ROWS)]
        
        self.is_first_click = True
        self.is_playing = True
        
        self.opened_tile_count = 0
        self.flags_left = self.BOMBS_COUNT
        
        self.bfs_visited = [[False for j in range(self.COLS)] for i in range(self.ROWS)]

        for i in range(self.ROWS):
            for j in range(self.COLS):
                tile = Tile(self.tiles_frame)

                tile.grid(row = i, column = j)
                tile.bind('<Button-1>', lambda event, tile = tile, i = i, j = j: self.open_tile(tile, i, j))
                tile.bind('<Button-3>', lambda event, tile = tile: self.toggle_flag(tile))

                self.tiles[i][j] = tile
        
        self.control_frame = Frame(self)
        self.control_frame.pack(fill = 'both')

        self.timer = Label(self.control_frame, text = '00:00')
        self.timer.pack(side = 'left')

        self.reset_btn = Button(self.control_frame, text = 'Reset', command = self.reset_tiles)
        self.reset_btn.pack(side = 'right')

        self.info_disp_frame = Frame(self)
        self.info_disp_frame.pack(fill = 'both')

        self.open_tiles_count_label = Label(self.info_disp_frame, text = f'Opened Tiles: {self.opened_tile_count}')
        self.open_tiles_count_label.pack(side = 'left')

        self.flag_label = Label(self.info_disp_frame, text = f'Flags Left: {self.flags_left}')
        self.flag_label.pack(side = 'right')

        self.update_idletasks()
        self.geometry(f'{self.winfo_reqwidth()}x{self.winfo_reqheight()}+5+5')

        self.mainloop()
    
    def check_winning_state(self):
        return self.opened_tile_count == self.WINNING_TILE_COUNT
    
    def is_safe(self, i, j):
        return 0 <= i < self.ROWS and 0 <= j < self.COLS
    
    def count_neighbors(self, i, j):
        neighbor_count = 0

        for x in range(-1, 2):
            for y in range(-1, 2):
                if x == 0 and y == 0:
                    continue

                new_i, new_j = i + x, j + y

                if self.is_safe(new_i, new_j) and self.tiles[new_i][new_j].get_value() == 'B':
                    neighbor_count += 1
        
        return neighbor_count
    
    def reset_tiles(self):
        self.opened_tile_count = 0
        self.flags_left = self.BOMBS_COUNT
        
        self.is_first_click = True
        self.is_playing = True
        
        self.open_tiles_count_label.config(text = f'Opened Tiles: {self.opened_tile_count}')
        self.flag_label.config(text = f'Flags Left: {self.flags_left}')
        
        [self.tiles[i][j].reset_tile() for i in range(self.ROWS) for j in range(self.COLS)]
        self.bfs_visited = [[False for j in range(self.COLS)] for i in range(self.ROWS)]
    
    def initialize_bombs(self, x, y):
        self.bombs_locs = random.sample([(i, j) for i in range(self.ROWS) for j in range(self.COLS) if (i, j) != (x, y)], self.BOMBS_COUNT)

        [self.tiles[i][j].set_value('B') for i, j in self.bombs_locs]

        for i in range(self.ROWS):
            for j in range(self.COLS):
                if self.tiles[i][j].get_value() != 'B':
                    neighbor_count = self.count_neighbors(i, j)
                    value = '' if neighbor_count == 0 else f'{neighbor_count}'
                    
                    self.tiles[i][j].set_value(value)
    
    def open_zero_tiles(self, init_i, init_j):
        tiles_to_open = deque([(init_i, init_j)])
        self.bfs_visited[init_i][init_j] = True

        while tiles_to_open:
            i, j = tiles_to_open.popleft()
            self.bfs_visited[i][j] = True
            
            for x, y in self.ALL_DIRS:
                new_i, new_j = i + x, j + y

                if self.is_safe(new_i, new_j) and not self.bfs_visited[new_i][new_j]:
                    new_tile_value = self.tiles[new_i][new_j].get_value()

                    if new_tile_value == '' and (x, y) in self.ALL_DIRS:
                        tiles_to_open.append((new_i, new_j))
                    
                    elif new_tile_value != 'B' and not self.tiles[new_i][new_j].is_tile_open():
                        self.tiles[new_i][new_j].force_open()
                        self.opened_tile_count += 1
            
            if not self.tiles[i][j].is_tile_open():
                self.tiles[i][j].force_open()
                self.opened_tile_count += 1

    def open_tile(self, tile, i, j):
        if self.is_playing:
            thread = Thread(target = self.open_zero_tiles, args = (i, j))
            
            if self.is_first_click:
                self.is_first_click = False
                self.initialize_bombs(i, j)
            
            if not tile.get_flag():
                tile_value = tile.get_value()

                if tile_value == 'B':
                    for x, y in self.bombs_locs:
                        self.tiles[x][y].display_bomb()
                    
                    self.is_playing = False
                
                elif tile_value == '':
                    thread.run()
                
                else:
                    tile.open_tile()
                    self.opened_tile_count += 1
                    
                    tile.display_value()
            
            while thread.is_alive():
                thread.join(2)
            
            if self.check_winning_state():
                print('Won!!')
            
            self.open_tiles_count_label.config(text = f'Opened Tiles: {self.opened_tile_count}')
    
    def toggle_flag(self, tile):
        if self.is_playing and not tile.is_tile_open():
            self.flags_left += (1 if tile.is_tile_flagged() else -1)
            self.flag_label.config(text = f'Flags Left: {self.flags_left}')
            tile.toggle_flag()

if __name__ == '__main__':
    Land(9, 9)