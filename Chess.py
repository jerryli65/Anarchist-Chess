# FILE AUTHOR: Jerry Li
# Credit for the original file goes to the user ransurf: https://github.com/ransurf
# This personal project has been adapted from ransurf in the following ways:
#     1. Cleaner code and organization, including refactoring.
#     2. Personal additions to the program
# `       a. Prevents castling when respective rook has already moved
#         b. Fixed illegal responses to "check" (not including castling)
#         c. Lichess.org Anarcandy piece set, owned by Lichess.org
#         d. Support to resign, draw, or create new game
# Future updates:
#         a. Two moves per turn, utilizing the concept of "premove"
#         b. Fix the infinite loop that occurs when the touchmove rule is violated
#         c. Support for the en passant rule
#         d. Forced en passant
#         e. Visual indicator of how the "horsey" moves
#         f. Castling through check, out of check, into check

import tkinter as tk
import string  # for a string to store alphabet
import os, sys  # help with importing images
from PIL import Image, ImageTk  # help with implementing images into GUI
from PIL.ImageTk import PhotoImage


class Board(tk.Frame):

    def __init__(self, parent):  # self=Frame, parent=root

        # initialization of Frame
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.length = 8
        self.width = 8
        self.config(height=100 * self.length, width=100 * self.width)
        self.pack()

        # attributes of the board
        self.square_color = None
        self.squares = {}  # stores squares with pos as key and button as value
        self.ranks = string.ascii_lowercase[0:8]  # a to h
        self.white_images = {}  # stores images of pieces
        self.black_images = {}

        # for convenience when calling all white or black pieces
        # pyimage2 = "nothing" square, corresponds to "blank.png"
        # then I didn't want to deal with copy-pasting shenanigans so I start black pieces at 8 and skip 9
        # may eventually come back and tidy that naming scheme
        self.white_pieces = ["pyimage1", "pyimage3", "pyimage4", "pyimage5", "pyimage6", "pyimage7"]
        self.black_pieces = ["pyimage8", "pyimage10", "pyimage11", "pyimage12", "pyimage13", "pyimage14"]
        self.buttons_pressed = 0
        self.turns = 0

        # each turn moves a piece on a square to a different square
        self.sq1 = None  # first square clicked
        self.sq2 = None
        self.sq1_button = None  # button associated with the square clicked
        self.sq2_button = None
        self.piece_color = None

        # castling rights
        self.castleable_long_white = True
        self.castleable_short_white = True
        self.castleable_long_black = True
        self.castleable_short_black = True

        self.set_squares()

    def select_piece(self, button):  # called when a square button is pressed, consists of majority of the movement code

        # what color is the piece that was just pressed?
        if button["image"] in self.white_pieces and self.buttons_pressed == 0:  # checks color of first piece
            self.piece_color = "white"
        elif button["image"] in self.black_pieces and self.buttons_pressed == 0:
            self.piece_color = "black"

        if (self.piece_color == "white" and self.turns % 2 == 0) or \
                (self.piece_color == "black" and self.turns % 2 == 1) or \
                self.buttons_pressed == 1:  # makes sure player only moves on their turn
            if self.buttons_pressed == 0:  # stores square and button of first square selected
                self.sq1 = list(self.squares.keys())[
                    list(self.squares.values()).index(button)]  # retrieves pos of piece
                self.sq1_button = button
                self.buttons_pressed += 1

            elif self.buttons_pressed == 1:  # stores square and button of second square selected
                self.sq2 = list(self.squares.keys())[list(self.squares.values()).index(button)]
                self.sq2_button = button
                if self.sq2 == self.sq1:  # prevents self-destruction and allows the user to choose a new piece
                    self.buttons_pressed = 0
                    return

                if self.allowed_piece_move() and self.friendly_fire() is False:  # makes sure the move is "legal"
                    # stores current square values for future use
                    # ensures that multiple illegal moves can be made in a row without losing original state
                    prev_sq1 = self.sq1
                    prev_sq1_button_piece = self.sq1_button["image"]
                    prev_sq2 = self.sq2
                    prev_sq2_button_piece = self.sq2_button["image"]

                    # moves the piece in square 1 to square 2 and clears square 1
                    self.squares[self.sq2].config(image=self.sq1_button["image"])  # moves piece in sq1 to sq2
                    self.squares[self.sq2].image = self.sq1_button["image"]
                    self.squares[self.sq1].config(image=self.white_images["blank.png"])  # clears sq1
                    self.squares[self.sq1].image = self.white_images["blank.png"]

                    if self.in_check():  # the king may be moving into check, we can't allow that
                        self.squares[prev_sq2].config(image=prev_sq2_button_piece)
                        self.squares[prev_sq2].image = prev_sq2_button_piece
                        self.squares[prev_sq1].config(image=prev_sq1_button_piece)
                        self.squares[prev_sq1].image = prev_sq1_button_piece
                        self.buttons_pressed = 0
                        return

                    else:  # runs if king is not in check, checks if kings or rooks have moved, preventing castling in the future
                        self.buttons_pressed = 0
                        self.turns += 1
                        if (button["image"] == "pyimage5" and prev_sq2.count("8") == 1) or (
                                button["image"] == "pyimage12" and prev_sq2.count(
                            "1") == 1):  # checks for possible pawn promotion
                            self.promotion_menu(self.piece_color)

        else:
            self.buttons_pressed = 0
            return

    def promotion_menu(self, color):  # creates menu to choose what piece to change the pawn to
        """Creates and displays a promotion menu for the user to pick a piece to promote to.

        :param color: A string that passes the piece color for accurate promotion icon colors"""

        def generate_promo_piece(piece):
            """Replaces the Button on the promotion square with the chosen promoted piece

            The function also destroys the promotion window and allows the game to continue"""
            self.squares[self.sq2].config(image=piece)
            self.squares[self.sq2].image = piece
            promo.destroy()
            return

        def display_promo_menu(color):
            """Displays the promotion menu with correct color

            :param color: A string that passes the piece color for accurate promotion icon colors"""
            if color == "white":
                promo_knight = tk.Button(promo, text="Knight", command=lambda: generate_promo_piece(
                    "pyimage4"))  # triggers generate_promo_piece function when selected
                promo_knight.grid(row=0, column=0)
                promo_bishop = tk.Button(promo, text="Bishop", command=lambda: generate_promo_piece("pyimage1"))
                promo_bishop.grid(row=0, column=1)
                promo_rook = tk.Button(promo, text="Rook", command=lambda: generate_promo_piece("pyimage7"))
                promo_rook.grid(row=1, column=0)
                promo_queen = tk.Button(promo, text="Queen", command=lambda: generate_promo_piece("pyimage6"))
                promo_queen.grid(row=1, column=1)
            else:
                promo_knight = tk.Button(promo, text="Knight", command=lambda: generate_promo_piece("pyimage11"))
                promo_knight.grid(row=0, column=0)
                promo_bishop = tk.Button(promo, text="Bishop", command=lambda: generate_promo_piece("pyimage8"))
                promo_bishop.grid(row=0, column=1)
                promo_rook = tk.Button(promo, text="Rook", command=lambda: generate_promo_piece("pyimage14"))
                promo_rook.grid(row=1, column=0)
                promo_queen = tk.Button(promo, text="Queen", command=lambda: generate_promo_piece("pyimage13"))
                promo_queen.grid(row=1, column=1)

        promo = tk.Tk()  # creates a new menu with buttons depending on pawn color
        promo.title("Choose what to promote your pawn to")
        display_promo_menu(color)
        promo.mainloop()
        return

    def friendly_fire(self):  # prevents capturing your own pieces
        """Prevents capturing your own pieces.

        @:return Boolean value determining whether 'friendly fire' has occurred, i.e. white tries to capture whtie"""
        piece_2_color = self.sq2_button["image"]
        return (self.piece_color == "white" and piece_2_color in self.white_pieces) or (
                    self.piece_color == "black" and piece_2_color in self.black_pieces)

    def clear_path(self, piece):  # makes sure that the squares in between sq1 and sq2 aren't occupied
        """Ensures that the selected piece does not have occupied squares between sq1 and sq2

        :param piece: string for the piece i.e. 'rook'"""
        # pieces that move left to right OR up to down (rook and queen)
        if piece == "rook" or piece == "queen":
            # clear path along the vertical axis
            if self.sq1[0] == self.sq2[0]:
                pos1 = min(int(self.sq1[1]), int(self.sq2[1]))
                pos2 = max(int(self.sq1[1]), int(self.sq2[1]))
                for i in range(pos1 + 1, pos2):
                    square_on_path = self.squares[self.sq1[0] + str(i)].cget("image")
                    if square_on_path != "pyimage2":
                        return False

            # clear path along the horizontal axis
            elif self.sq1[1] == self.sq2[1]:
                pos1 = min(self.ranks.find(self.sq1[0]), self.ranks.find(self.sq2[0]))
                pos2 = max(self.ranks.find(self.sq1[0]), self.ranks.find(self.sq2[0]))
                for i in range(pos1 + 1, pos2):
                    square_on_path = self.squares[self.ranks[i] + self.sq1[1]].cget("image")
                    if square_on_path != "pyimage2":
                        return False

        # pieces that move diagonally
        if piece == "bishop" or piece == "queen":
            x1 = self.ranks.find(self.sq1[0])
            x2 = self.ranks.find(self.sq2[0])
            y1 = int(self.sq1[1])
            y2 = int(self.sq2[1])

            if y1 < y2:
                if x1 < x2:  # NE direction
                    for x in range(x1 + 1, x2):
                        y1 += 1
                        square_on_path = self.squares[self.ranks[x] + str(y1)].cget("image")
                        if square_on_path != "pyimage2":
                            return False
                elif x1 > x2:  # NW direction
                    for x in range(x1 - 1, x2, -1):
                        y1 += 1
                        square_on_path = self.squares[self.ranks[x] + str(y1)].cget("image")
                        if square_on_path != "pyimage2":
                            return False
            elif y1 > y2:
                if x1 < x2:  # SE direction
                    for x in range(x1 + 1, x2):
                        y1 -= 1
                        square_on_path = self.squares[self.ranks[x] + str(y1)].cget("image")
                        if square_on_path != "pyimage2":
                            return False
                if x1 > x2:  # SW direction
                    for x in range(x1 - 1, x2, -1):
                        y1 -= 1
                        square_on_path = self.squares[self.ranks[x] + str(y1)].cget("image")
                        if square_on_path != "pyimage2":
                            return False
        return True

    def allowed_piece_move(self):  # checks whether the piece can move to square 2 based on their movement capabilities
        # TODO: It may be here that we fix Touchmove...may have to do with False
        """Checks whether the piece on pos1 can go to pos2 based on their movement capabilities.

        :return Boolean value for whether the move is allowed.
        If it isn't, the program simply allows the user to choose a different square."""

        # redefine pyimage for readability; now we can refer to them simply as pieces on the board
        wb, wk, wn, wp, wq, wr = "pyimage1", "pyimage3", "pyimage4", "pyimage5", "pyimage6", "pyimage7"
        bb, bk, bn, bp, bq, br = "pyimage8", "pyimage10", "pyimage11", "pyimage12", "pyimage13", "pyimage14"

        # If the supposed piece is Nothing then there is no way it is a legal move
        if self.sq1_button["image"] == "pyimage2":  # or self.sq1_button["image"] == "pyimage9":
            return False

        # bishop's move: the change in x (rank) is the same as the change in y (file)
        if (self.sq1_button["image"] == wb or self.sq1_button["image"] == bb) and self.clear_path(
                "bishop"):
            # if abs(int(self.sq1[1]) - int(self.sq2[1])) == abs(self.ranks.find(self.sq1[0]) - self.ranks.find(
            #  self.sq2[0])):
            #     return True
            return abs(int(self.sq1[1]) - int(self.sq2[1])) == abs(
                self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0]))

        # knight's move: if x changes by 1, then y changes by 2. Else if x changes by 2, then y changes by 1
        if self.sq1_button["image"] == wn or self.sq1_button["image"] == bn:
            if (abs(int(self.sq1[1]) - int(self.sq2[1])) == 2) and (
                    abs(self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0])) == 1):  # allows tall L moves
                return True
            if (abs(int(self.sq1[1]) - int(self.sq2[1])) == 1) and (
                    abs(self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0])) == 2):  # allows wide L moves
                return True

        # King's move: it may be a 1 square adjacent move OR a castle
        # we check adjacent attempt first because castle() catches all other move attempts
        # TODO: Potentially this is where I fix illegal castle (including in, out of, through check; potentially rook moved)
        if self.sq1_button["image"] == wk or self.sq1_button["image"] == bk:  # king movement
            if (abs(int(self.sq1[1]) - int(self.sq2[1])) < 2) and (
            abs(self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0]))) < 2:
                if self.sq1_button["image"] == wk:
                    self.disallow_castle("white", "wk", "short")  # parameter 'short' is unused
                else:
                    self.disallow_castle("black", "bk", "short")
                return True
            if self.castle() is True:
                return True

        # White pawn movement: If it starts on the 2nd rank, it can move two squares, else 1 square
        # It may capture sideways
        # TODO: En passant
        if self.sq1_button["image"] == wp:
            if "2" in self.sq1:  # allows for 2 space jump from starting pos
                if (int(self.sq1[1]) + 1 == int(self.sq2[1]) or int(self.sq1[1]) + 2 == int(self.sq2[1])) and \
                        self.sq1[0] == self.sq2[0] and self.sq2_button["image"] == "pyimage2":  # allows 2 sq movement
                    in_front = self.squares[self.sq1[0] + str(int(self.sq1[1]) + 1)]
                    if in_front["image"] == "pyimage2":  # makes sure that there is no piece blocking path
                        return True
            if int(self.sq1[1]) + 1 == int(self.sq2[1]) and self.sq1[0] == self.sq2[0] and \
                    self.sq2_button["image"] == "pyimage2":  # allows 1 sq movement
                return True
            if int(self.sq1[1]) + 1 == int(self.sq2[1]) and \
                    (abs(self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0]))) == 1 and \
                    self.sq2_button["image"] != "pyimage2":  # allows the capturing of diagonal pieces
                return True

        # Black pawn movement: If it starts on the 7th rank, it can move two squares, else 1 square
        # It may capture sideways
        # TODO: En passant
        if self.sq1_button["image"] == bp:
            if "7" in self.sq1:  # allows for 2 space jump from starting pos
                if (int(self.sq1[1]) == int(self.sq2[1]) + 1 or int(self.sq1[1]) == int(self.sq2[1]) + 2) and \
                        self.sq1[0] == self.sq2[0] and self.sq2_button["image"] == "pyimage2":
                    return True
            if int(self.sq1[1]) == int(self.sq2[1]) + 1 and self.sq1[0] == self.sq2[0] and \
                    self.sq2_button["image"] == "pyimage2":
                return True
            if int(self.sq1[1]) == int(self.sq2[1]) + 1 and \
                    abs(self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0])) == 1 \
                    and self.sq2_button["image"] != "pyimage2":  # allows the capturing of diagonal pieces
                return True

        # Queen movement: Can move within the same rank, the same file, the same diagonal
        # It is the combination of a rook and a bishop
        if (self.sq1_button["image"] == wq or self.sq1_button["image"] == bq) and self.clear_path("queen"):
            if int(self.sq1[1]) == int(self.sq2[1]) or self.sq1[0] == self.sq2[
                0]:  # only allows movement within same rank or file
                return True
            if abs(int(self.sq1[1]) - int(self.sq2[1])) == abs(
                    self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0])):
                return True

        # Rook movement: Can move within the same rank or the same file
        if self.sq1_button["image"] == wr or self.sq1_button["image"] == br:
            if (int(self.sq1[1]) == int(self.sq2[1]) or self.sq1[0] == self.sq2[0]) and self.clear_path("rook"):
                if self.sq1 == "a1":
                    self.disallow_castle("white", "wr", "long")
                if self.sq1 == "h1":
                    self.disallow_castle("white", "wr", "short")
                if self.sq1 == "a8":
                    self.disallow_castle("black", "br", "long")
                if self.sq1 == "h8":
                    self.disallow_castle("black", "br", "short")
                return True

        # Well, then whatever piece is currently clicked on pos1 cannot go to pos2
        return False

    def disallow_castle(self, color, piece, direction):
        if color == "white":
            if piece == "wk":
                self.castleable_short_white = False
                self.castleable_long_white = False
                return
            if direction == "short":
                self.castleable_short_white = False
            else:
                self.castleable_long_white = False
        else:
            if piece == "bk":
                self.castleable_short_black = False
                self.castleable_long_black = False
                return
            if direction == "short":
                self.castleable_short_black = False
            else:
                self.castleable_long_black = False
        return

    def castle(self):  # checks to see if the move entails a castle, and if a castle is allowed
        """Checks to see if castle is allowed, i.e. king hasn't moved, rook in question hasn't moved, opponent doesn't see path
        If castle is allowed, then hard-config the pieces.

        Called from function allowed_piece_move() when a castle is attempted by either side
        The game piece that this function acts on is thus a white king or black king, assigned already

        Updates the attribute \"castled\" as needed.

        :return Boolean value representing whether the player successfully castled or not.
        """
        # TODO: Main error for castling out of check
        # print("castle")
        # if self.in_check():
        #     print("is in")
        #     return False
        if self.castleable_short_white and self.sq2 == "g1":
            for x in range(5, 7):
                square_button = self.squares[self.ranks[x] + str(1)]
                if square_button["image"] != "pyimage2":
                    return False
                self.squares["h1"].config(image="pyimage2")
                self.squares["h1"].image = "pyimage2"
                self.squares["f1"].config(image="pyimage7")
                self.squares["f1"].image = "pyimage7"
                return True
        if self.castleable_long_white and self.sq2 == "c1" or self.sq2 == "b1":  # some people castle incorrectly with b1, but the software usually allows it
            for x in range(1,
                           4):  # checks to see if squares in between rook and king are empty and are not a possible move for opponent
                square_button = self.squares[self.ranks[x] + str(1)]  # append str(1) gives a1, b1, etc
                if square_button["image"] != "pyimage2":
                    return False
                self.squares["a1"].config(image="pyimage2")
                self.squares["a1"].image = "pyimage2"
                self.squares["d1"].config(image="pyimage7")
                self.squares["d1"].image = "pyimage7"
                return True
        if self.castleable_short_black and self.sq2 == "g8":
            for x in range(5, 7):
                square_button = self.squares[self.ranks[x] + str(8)]
                if square_button["image"] != "pyimage2":
                    return False
                self.squares["h8"].config(image="pyimage2")
                self.squares["h8"].image = "pyimage2"
                self.squares["f8"].config(image="pyimage14")
                self.squares["f8"].image = "pyimage14"
                return True
        if self.castleable_long_black and self.sq2 == "c8" or self.sq2 == "b8":
            for x in range(5, 7):
                square_button = self.squares[self.ranks[x] + str(8)]
                if square_button["image"] != "pyimage2":
                    return False
                self.squares["h8"].config(image="pyimage2")
                self.squares["h8"].image = "pyimage2"
                self.squares["f8"].config(image="pyimage14")
                self.squares["f8"].image = "pyimage14"
                return True
        else:
            return False

    def in_check(self):
        """Checks if either King is in check; if one is, the function prevents illegal moves

        """

        # stores current square values for future use
        # ensures that multiple illegal moves can be made in a row without losing original state
        previous_sq1 = self.sq1
        previous_sq1_button = self.sq1_button
        previous_sq2 = self.sq2
        previous_sq2_button = self.sq2_button

        def revert_to_previous_values():
            """Reverts the state of the squares to the previous square and button

            :return Boolean value whether King is in \"check\" """

            self.sq1 = previous_sq1
            self.sq1_button = previous_sq1_button
            self.sq2 = previous_sq2
            self.sq2_button = previous_sq2_button

        if self.piece_color == "white":
            self.sq2 = self.find_king("pyimage3")

            # iterating through each square on the board
            for key in self.squares:
                self.sq1 = key
                self.sq1_button = self.squares[self.sq1]
                # if the square's piece is black, then check if the King is on the piece's path, indicating "check"
                if self.sq1_button["image"] in self.black_pieces:
                    if self.allowed_piece_move():
                        return True

        if self.piece_color == "black":
            self.sq2 = self.find_king("pyimage10")
            for key in self.squares:
                self.sq1 = key
                self.sq1_button = self.squares[self.sq1]
                if self.sq1_button["image"] in self.white_pieces:
                    if self.allowed_piece_move():
                        return True

        # Then neither King was in check this turn, so revert to previous squares and return False
        revert_to_previous_values()
        return False

    def find_king(self, king):
        """Finds the square the king is on. Primarily used for determining if either King is in check each move

        :parameter king: refers to the name of the King as a string, which may be white ("pyimage3") or black ("pyimage10")

        :return King coordinates as a string, ex: \"e2\""""
        for square in self.squares:  # squares is list of coords, so square is a coord, ex. e2
            button = self.squares[square]  # button contains an image (piece) and a coord
            if button["image"] == king:  # checks if the piece's coord is that of the King
                return square

    def set_squares(self):  # fills frame with buttons representing squares
        """Fills frame with 64 buttons in 8x8 grid which represent squares. They alternate in color with h1 being white.

        :return void
        """
        for x in range(8):
            for y in range(8):
                if x % 2 == 0 and y % 2 == 0:  # alternates between dark/light tiles
                    self.square_color = "green"
                elif x % 2 == 1 and y % 2 == 1:
                    self.square_color = "green"
                else:
                    self.square_color = "gray"

                # highlights the selected starting square to indicate that choice
                # the Touchmove rule requires the user to move the piece highlighted, if it is legal
                # TODO: Fix issue where touchmove crashes program when no legal moves
                B = tk.Button(self, bg=self.square_color, activebackground="purple")
                B.grid(row=8 - x, column=y)
                pos = self.ranks[y] + str(x + 1)
                self.squares.setdefault(pos, B)  # creates list of square positions
                self.squares[pos].config(command=lambda key=self.squares[pos]: self.select_piece(key))

    def import_pieces(self):  # opens and stores images of pieces and prepares the pieces for the game for both sides
        """Opens and stores images of pieces. Gets ready to put pieces on initial squares.

        The programmer may wish to adjust the filepaths depending on the file location of the pieces.

        :return void
        """
        path = os.path.join(os.path.dirname(__file__), "White")  # stores white pieces images into dicts
        w_dirs = os.listdir(path)
        for file in w_dirs:
            img = Image.open(path + "\\" + file)
            img = img.resize((80, 80), Image.ANTIALIAS)
            img = ImageTk.PhotoImage(image=img)
            self.white_images.setdefault(file, img)

        path = os.path.join(os.path.dirname(__file__), "Black")  # stores black pieces images into dicts
        b_dirs = os.listdir(path)
        for file in b_dirs:
            img = Image.open(path + "\\" + file)
            img = img.resize((80, 80), Image.ANTIALIAS)
            img = ImageTk.PhotoImage(image=img)
            self.black_images.setdefault(file, img)

    def set_starting_position(self):  # places pieces in starting positions
        """Places pieces in their starting position.

        :return void
        """

        # organizing the white pieces
        dict_rank1_pieces = {"a1": "r.png", "b1": "n.png", "c1": "b.png", "d1": "q.png", "e1": "k.png", "f1": "b.png",
                             "g1": "n.png", "h1": "r.png"}
        dict_rank2_pieces = {"a2": "p.png", "b2": "p.png", "c2": "p.png", "d2": "p.png", "e2": "p.png", "f2": "p.png",
                             "g2": "p.png", "h2": "p.png"}
        # organizing the black pieces
        dict_rank7_pieces = {"a7": "p.png", "b7": "p.png", "c7": "p.png", "d7": "p.png", "e7": "p.png", "f7": "p.png",
                             "g7": "p.png", "h7": "p.png"}
        dict_rank8_pieces = {"a8": "r.png", "b8": "n.png", "c8": "b.png", "d8": "q.png", "e8": "k.png", "f8": "b.png",
                             "g8": "n.png", "h8": "r.png"}

        # inserting images into buttons
        for key in dict_rank1_pieces:
            starting_piece = dict_rank1_pieces[key]
            self.squares[key].config(image=self.white_images[starting_piece])
            self.squares[key].image = self.white_images[starting_piece]

        for key in dict_rank2_pieces:
            starting_piece = dict_rank2_pieces[key]
            self.squares[key].config(image=self.white_images[starting_piece])
            self.squares[key].image = self.white_images[starting_piece]

        for key in dict_rank7_pieces:
            starting_piece = dict_rank7_pieces[key]
            self.squares[key].config(image=self.black_images[starting_piece])
            self.squares[key].image = self.black_images[starting_piece]

        for key in dict_rank8_pieces:
            starting_piece = dict_rank8_pieces[key]
            self.squares[key].config(image=self.black_images[starting_piece])
            self.squares[key].image = self.black_images[starting_piece]

        for rank in range(3, 7):  # fill ranks 3,4,5,6 with blank pieces
            for file in range(8):  # there are 8 squares (buttons) in each rank
                starting_piece = "blank.png"
                pos = self.ranks[file] + str(rank)
                self.squares[pos].config(image=self.white_images[starting_piece])
                self.squares[pos].image = self.white_images[starting_piece]


root = tk.Tk()  # creates main window with the board and creates board object
root.geometry("800x800")
board = Board(root)
print(board.ranks)
board.import_pieces()
board.set_starting_position()

button_resign = tk.Button(root, text="RESIGN", height=1, width=5, command=lambda: board.set_squares())
button_resign.pack()
button_draw = tk.Button(root, text="DRAW", height=1, width=5, command=lambda: board.set_squares())
button_draw.pack()
button_newgame = tk.Button(root, text="NEW GAME", height=1, width=10, command=lambda: board.set_squares())
button_newgame.pack()

board.mainloop()
