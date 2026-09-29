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