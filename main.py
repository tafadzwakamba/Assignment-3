import tkinter as tk
from tkinter import filedialog, messagebox
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
        self.image = ImageTk.PhotoImage(original_img)  # Tkinter-compatible image

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


            # ========================================
            #OOP: Inheritance & Polymorphism
            #========================================
            class Transformation:
                """Base class for transformations applied to tiles."""
                def apply(self, tile):
                    raise NotImplementedError("Subclasses should implement this method.")

            class SwapTransform(Transformation):
                def apply(self, app):
                    r1, c1 = random.randint(0, app.N-1), random.randint(0, app.N-1)
                    r2, c2 = random.randint(0, app.N-1), random.randint(0, app.N-1)
                    # Swap positions of tiles
                    app.tiles[r1][c1], app.tiles[r2][c2] = app.tiles[r2][c2], app.tiles[r1][c1]
                    app.tiles[r1][c1].current_r, app.tiles[r1][c1].current_c = r1, c1
                    app.tiles[r2][c2].current_r, app.tiles[r2][c2].current_c = r2, c2

                class RotateTransform(Transformation):
                    def apply(self, app):
                        r, c = random.randint(0, app.N-1), random.randint(0, app.N-1)
                        rotations = random.choice([1, 2, 3])  # Rotate by 90, 180, or 270 degrees
                        app.tiles[r][c].rotate(rotations)

                class FlipTransform(Transformation):
                    def apply(self, app):
                        r, c = random.randint(0, app.N-1), random.randint(0, app.N-1)
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
        self.tiles = []  # 2D list to hold Tile objects
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
        self.btb_hint.config(text=f"Hint ({self.hints_remaining} left)"), state=tk.NORMAL

        # Load and prepare image (resize to 400x400 max, then crop to divide evenly)
        img = cv2.imread(file_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, _ = img.shape[:2]
        scale = min(400/w, 400/h)
        img = cv2.resize(img, (int(w*scale), int(h*scale)))

        h, w, _ = img.shape[:2]
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
        transform_count = {3: 6, 4: 12, 5: 20}[self.N] # Scale transformations by grid size[cite: 1]
        transforms = [SwapTransform(), RotateTransform(), FlipTransform()]
        for _ in range(transform_count):
            random.choice(transforms).apply(self)

        self.render_original()
        self.render_transformed()  
        
              