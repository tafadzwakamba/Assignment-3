import tkinter as tk
from tkinter import filedialog, messagebox
from abc import ABC, abstractmethod
from typing import cast
import cv2
import numpy as np
from PIL import Image, ImageTk
import random 


# ========================================
#OOP: Encapsulation & Class Interaction
#========================================
class Tile:
    """Represents the state and image data of a single tile in the puzzle."""
    def __init__(self, original_img, correct_r, correct_c):
        self.original_img = original_img.copy()  # Original image of the tile
        self.current_img = original_img.copy()   # Current image of the tile
        self.correct_r = correct_r        # Correct row position
        self.correct_c = correct_c        # Correct column position
        self.current_r = correct_r        # Current row position
        self.current_c = correct_c        # Current column position
        
        # FIXED: Converted the numpy array to a PIL Image first
        pil_image = Image.fromarray(original_img)
        self.image = ImageTk.PhotoImage(pil_image) 
        
    def is_correct(self):
        """Check if the tile is in home position with correct orientation."""
        position_match = (self.current_r == self.correct_r) and (self.current_c == self.correct_c)
        image_match = np.array_equal(np.array(self.current_img), np.array(self.original_img))
        return position_match and image_match

    def rotate(self, clockwise90_count):
        """Rotate the tile image."""
        for _ in range(clockwise90_count):
            self.current_img = cv2.rotate(self.current_img, cv2.ROTATE_90_CLOCKWISE)

    def flip(self, horizontal=True):
        """Flip the tile image."""
        flip_code = 1 if horizontal else 0
        self.current_img = cv2.flip(self.current_img, flip_code)


class OptionMenu:
    """Simple option-selector helper with ordered values and selected-state tracking."""

    def __init__(self, options=None, default=None):
        self._options = []
        self._selected_index = -1
        self.selected = None
        self.set_options(options or [], default=default)

    def set_options(self, options, default=None):
        """Replace the available options and choose a default selection."""
        self._options = list(options)
        if not self._options:
            self._selected_index = -1
            self.selected = None
            return

        if default is None:
            default = self._options[0]
        if default not in self._options:
            default = self._options[0]

        self._selected_index = self._options.index(default)
        self.selected = default

    def add_option(self, option):
        """Add a new option if it is not already present."""
        if option in self._options:
            return self.get_selected()
        self._options.append(option)
        if self._selected_index == -1:
            self._selected_index = 0
            self.selected = option
        return self.get_selected()

    def remove_option(self, option):
        """Remove an option and keep the current selection valid."""
        if option not in self._options:
            return False

        index = self._options.index(option)
        del self._options[index]

        if not self._options:
            self._selected_index = -1
            self.selected = None
            return True

        if self._selected_index > index:
            self._selected_index -= 1
        elif self._selected_index == index:
            self._selected_index = min(index, len(self._options) - 1)

        self.selected = self._options[self._selected_index]
        return True

    def get_options(self):
        """Return a copy of the current options list."""
        return list(self._options)

    def get_selected(self):
        """Return the currently selected option or None if empty."""
        if not self._options or self._selected_index < 0:
            return None
        return self._options[self._selected_index]

    def set_selected(self, value):
        """Set the selection to a known option value."""
        if value not in self._options:
            raise ValueError(f"Option {value!r} is not available.")
        self._selected_index = self._options.index(value)
        self.selected = value
        return value

    def __iter__(self):
        return iter(self._options)

    def __len__(self):
        return len(self._options)

    def __bool__(self):
        return bool(self._options)


# ========================================
#OOP: Inheritance & Polymorphism
#========================================
class Transformation(ABC):
    """Base class for transformations applied to tiles.

    Provides a safe default implementation so a transformation can be created
    without crashing when the puzzle is uninitialized or empty.
    """
    def apply(self, app):
        """Apply a mutation to the puzzle state.

        Subclasses override this method to perform actual tile mutations. The
        default implementation is intentionally a no-op so the base class can be
        used safely as a fallback.
        """
        if not hasattr(app, "tiles") or not app.tiles or not app.tiles[0]:
            return None
        return None


class SwapTransform(Transformation):
    """Swap two tiles in the puzzle grid."""
    def apply(self, app):
        if not app.tiles or not app.tiles[0]:
            return

        r1, c1 = random.randint(0, app.N - 1), random.randint(0, app.N - 1)
        r2, c2 = random.randint(0, app.N - 1), random.randint(0, app.N - 1)

        while (r1, c1) == (r2, c2):
            r2, c2 = random.randint(0, app.N - 1), random.randint(0, app.N - 1)

        app.tiles[r1][c1], app.tiles[r2][c2] = app.tiles[r2][c2], app.tiles[r1][c1]
        app.tiles[r1][c1].current_r, app.tiles[r1][c1].current_c = r1, c1
        app.tiles[r2][c2].current_r, app.tiles[r2][c2].current_c = r2, c2


class RotateTransform(Transformation):
    """Rotate a random tile by a random amount."""
    def apply(self, app):
        if not app.tiles or not app.tiles[0]:
            return

        r, c = random.randint(0, app.N - 1), random.randint(0, app.N - 1)
        rotations = random.choice([1, 2, 3])
        app.tiles[r][c].rotate(rotations)


class FlipTransform(Transformation):
    """Flip a random tile horizontally or vertically."""
    def apply(self, app):
        if not app.tiles or not app.tiles[0]:
            return

        r, c = random.randint(0, app.N - 1), random.randint(0, app.N - 1)
        horizontal = random.choice([True, False])
        app.tiles[r][c].flip(horizontal)


#========================================
#Core Application & GUI[cite: 1]
#========================================
class PuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HIT137 Image Puzzle Game")

        self.N = 3  # Default grid size[cite: 1]
        self.grid_size_var = tk.IntVar(value=self.N)
        self.moves = 0   
        self.hints_remaining = 3  # Original image for reference
        self.hint_active = False  # Size of each tile in pixels
        self.hint_target = None
        self.selected_tile = None
        self.is_solved = False  # Size of each tile in pixels

        self.original_image_cv = None  # Original image in OpenCV format
        self.tiles: list[list[Tile]] = []  # 2D list to hold Tile objects
        self.tk_original_img = None  # Original image in Tkinter format
        self.tk_tiles = []  # 2D list to hold Tkinter-compatible images of tiles

        self.setup_ui()

    def setup_ui(self):
        """Bulds Tkinter layout with controls and canvas for the puzzle."""
        ctrl_frame = tk.Frame(self.root)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(ctrl_frame, text="Grid:").pack(side=tk.LEFT)
        tk.OptionMenu(ctrl_frame, self.grid_size_var, 3, 4, 5).pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl_frame, text="Load Image", command=self.load_image).pack(side=tk.LEFT, padx=5)
        
        self.score_label = tk.Label(ctrl_frame, text="Moves: 0 | Incorrect: 0", font=("Arial", 10, "bold"))
        self.score_label.pack(side=tk.LEFT, padx=20)
        
        self.btn_hint = tk.Button(ctrl_frame, text="Hint (3 left)", command=self.use_hint)
        self.btn_hint.pack(side=tk.RIGHT, padx=5)
        tk.Button(ctrl_frame, text="Solve", command=self.solve_puzzle).pack(side=tk.RIGHT, padx=5)

        display_frame = tk.Frame(self.root)
        display_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        self.canvas_orig = tk.Canvas(display_frame, width=400, height=400, bg="lightgray")
        self.canvas_orig.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.canvas_trans = tk.Canvas(display_frame, width=400, height=400, bg="darkgray")
        self.canvas_trans.pack(side=tk.RIGHT, padx=10, pady=10)
        
        self.canvas_trans.bind("<Button-1>", self.on_left_click)
        self.canvas_trans.bind("<Button-3>", self.on_right_click)
        self.canvas_trans.bind("<Shift-Button-1>", self.on_shift_left_click) 
    def load_image(self):
        """Load an image file and initialize the puzzle."""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if not file_path:
            return

        # Load the image using OpenCV
        self.N = self.grid_size_var.get()
        self.moves = 0
        self.hints_remaining = 3
        self.hint_active = False
        self.is_solved = False
        self.selected_tile = None
        self.btn_hint.config(text=f"Hint ({self.hints_remaining} left)", state=tk.NORMAL)

        # Load and prepare image (resize to 400x400 max, then crop to divide evenly)
        img = cv2.imread(file_path)
        if img is None:
            messagebox.showerror("Load Image", f"Could not load image: {file_path}")
            return

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # FIXED: img.shape[:2] only returns 2 values (height, width). Removed the trailing '_'
        h, w = img.shape[:2]
        
        scale = min(400/w, 400/h)
        img = cv2.resize(img, (int(w*scale), int(h*scale)))

        # FIXED: removed the trailing '_' here as well
        h, w = img.shape[:2]
        
        self.tile_w = w // self.N
        self.tile_h = h // self.N
        img = img[0:self.tile_h*self.N, 0:self.tile_w*self.N]  # Crop to fit grid
        self.original_image_cv = img

        # Create tiles
        self.tiles = []
        for r in range(self.N):
            row = []
            for c in range(self.N):
                tile_img = img[r*self.tile_h:(r+1)*self.tile_h, c*self.tile_w:(c+1)*self.tile_w]
                row.append(Tile(tile_img, r, c))
            self.tiles.append(row)

        # Scramble
        transform_count = {3: 6, 4: 12, 5: 20}[self.N] # Scale transformations by grid size
        transforms = [SwapTransform(), RotateTransform(), FlipTransform()]
        for _ in range(transform_count):
            random.choice(transforms).apply(self)

        self.render_original()
        self.render_transformed()

    def render_original(self):
        """Displays static original image on the left."""
        if self.original_image_cv is None:
            self.canvas_orig.delete("all")
            return

        self.canvas_orig.delete("all")
        img_pil = Image.fromarray(self.original_image_cv)
        self.tk_original_img = ImageTk.PhotoImage(img_pil)
        self.canvas_orig.create_image(0, 0, anchor=tk.NW, image=self.tk_original_img)

    def render_transformed(self):
        """Displays interactive tiles, grids, hints, and ticks on the right."""
        self.canvas_trans.delete("all")
        self.tk_tiles = []
        incorrect_count = 0    

        for r in range(self.N):
            tk_row = []
            for c in range(self.N):
                tile = self.tiles[r][c]
                x, y = c * self.tile_w, r * self.tile_h
                
                pil_img = Image.fromarray(tile.current_img)
                tk_img = ImageTk.PhotoImage(pil_img)
                tk_row.append(tk_img)
                self.canvas_trans.create_image(x, y, anchor=tk.NW, image=tk_img)
                
                # Faint grid
                self.canvas_trans.create_rectangle(x, y, x+self.tile_w, y+self.tile_h, outline="black", dash=(2, 4))
                
                if tile.is_correct():
                    # Small green tick for correct tiles
                    self.canvas_trans.create_text(x+self.tile_w-15, y+15, text="✔", fill="green", font=("Arial", 16, "bold"))
                else:
                    incorrect_count += 1
                    
                # Highlight selection
                if self.selected_tile == (r, c):
                    self.canvas_trans.create_rectangle(x, y, x+self.tile_w, y+self.tile_h, outline="red", width=3)
            self.tk_tiles.append(tk_row)

        self.score_label.config(text=f"Moves: {self.moves} | Incorrect: {incorrect_count}")     

        # Draw Hint Circles
        if self.hint_active and self.hint_target:
            hr, hc = self.hint_target
            # Circle on transformed image
            x, y = hc * self.tile_w + self.tile_w//2, hr * self.tile_h + self.tile_h//2
            self.canvas_trans.create_oval(x-15, y-15, x+15, y+15, outline="blue", width=3)
            
            # Circle on original image's home position
            correct_r = self.tiles[hr][hc].correct_r
            correct_c = self.tiles[hr][hc].correct_c
            ox, oy = correct_c * self.tile_w + self.tile_w//2, correct_r * self.tile_h + self.tile_h//2
            self.canvas_orig.create_oval(ox-15, oy-15, ox+15, oy+15, outline="blue", width=3)

        if incorrect_count == 0 and not self.is_solved and self.moves > 0:
            self.is_solved = True
            messagebox.showinfo("Puzzle Solved!", f"Congratulations! You restored the picture in {self.moves} moves.")

    def record_move(self):
        """Increments score and clears hints after a move."""
        self.moves += 1
        if self.hint_active:
            self.hint_active = False
            self.hint_target = None
            self.render_original() # Clear hint from left image
        self.render_transformed()

    def get_tile_index(self, event):
        if self.is_solved or not self.tiles: return None
        c = event.x // self.tile_w
        r = event.y // self.tile_h
        if 0 <= r < self.N and 0 <= c < self.N:
            return (r, c)
        return None

    def on_left_click(self, event):
        idx = self.get_tile_index(event)
        if not idx: return
        r, c = idx
        
        if self.selected_tile is None:
            self.selected_tile = (r, c)
            self.render_transformed()
        elif self.selected_tile == (r, c):
            self.selected_tile = None # Deselect
            self.render_transformed()
        else:
            # Swap tiles
            sr, sc = self.selected_tile
            self.tiles[sr][sc], self.tiles[r][c] = self.tiles[r][c], self.tiles[sr][sc]
            self.tiles[sr][sc].current_r, self.tiles[sr][sc].current_c = sr, sc
            self.tiles[r][c].current_r, self.tiles[r][c].current_c = r, c
            self.selected_tile = None
            self.record_move() 

    def on_right_click(self, event):
        idx = self.get_tile_index(event)
        if not idx: return
        self.tiles[idx[0]][idx[1]].rotate(1) # Rotate 90 deg clockwise[cite: 1]
        self.record_move()

    def on_shift_left_click(self, event):
        idx = self.get_tile_index(event)
        if not idx: return
        self.tiles[idx[0]][idx[1]].flip(horizontal=True) # Flip horizontally[cite: 1]
        self.record_move()

    def use_hint(self):
        if self.hints_remaining <= 0 or self.is_solved or not self.tiles: return
        
        incorrect_tiles = [(r, c) for r in range(self.N) for c in range(self.N) if not self.tiles[r][c].is_correct()]
        if not incorrect_tiles: return
        
        self.hints_remaining -= 1
        self.btn_hint.config(text=f"Hint ({self.hints_remaining} left)")
        if self.hints_remaining == 0:
            self.btn_hint.config(state=tk.DISABLED) # Disable when empty[cite: 1]
            
        self.hint_target = random.choice(incorrect_tiles)
        self.hint_active = True
        self.render_original()
        self.render_transformed()

    def solve_puzzle(self):
        """Instantly undoes all remaining transformations and clears score[cite: 1]."""
        if not self.tiles or self.is_solved: return
        
        # Reset to home states
        new_tiles: list[list[Tile | None]] = [[None] * self.N for _ in range(self.N)]
        for r in range(self.N):
            for c in range(self.N):
                tile = self.tiles[r][c]
                tile.current_img = tile.original_img.copy()
                tile.current_r = tile.correct_r
                tile.current_c = tile.correct_c
                new_tiles[tile.correct_r][tile.correct_c] = tile
                
        self.tiles = [row for row in new_tiles if row]  # type: ignore[assignment]
        self.moves = 0
        self.selected_tile = None
        self.hint_active = False
        self.render_original()
        self.render_transformed()

if __name__ == "__main__":
    root = tk.Tk()
    app = PuzzleApp(root)
    root.mainloop()    