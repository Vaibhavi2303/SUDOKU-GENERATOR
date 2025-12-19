import pygame
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import mysql.connector as sqlcon
import random
import time

# Pygame Sudoku Constants
GRID_SIZE=9
WIDTH=540
HEIGHT=600
SQUARE_SIZE=WIDTH // GRID_SIZE
FPS=60
MAX_WRONG = 3

# Pygame Sudoku Colors
WHITE=(255, 255, 255)
BLACK=(0, 0, 0)
LIGHT_PURPLE = (70, 0, 100) # Dark purple for background
GRAY=(200, 200, 200)
BLUE=(0, 150, 255) # Selection color
RED=(255, 100, 100) # Wrong attempt color
GREEN=(100, 255, 100)
HINT_COLOR=(255, 200, 50) # Gold/Yellow for user-entered numbers for better contrast/distinction

# Sudoku Logic Functions

def is_valid(board, num, pos):
    """Checks if placing num at pos is valid according to Sudoku rules."""
    row, col = pos
    # Check row
    for i in range(GRID_SIZE):
        if board[row][i] == num and col != i: return False
    # Check column
    for i in range(GRID_SIZE):
        if board[i][col] == num and row != i: return False
    # Check 3x3 box
    box_x = col // 3
    box_y = row // 3
    for i in range(box_y * 3, box_y * 3 + 3):
        for j in range(box_x * 3, box_x * 3 + 3):
            if board[i][j] == num and (i, j) != pos: return False
    return True

def find_empty(board):
    """Finds the next empty cell (0) on the board."""
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if board[i][j] == 0: return (i, j)
    return None

def solve(board):
    """Solves the Sudoku board using backtracking (used to verify solvable)."""
    find = find_empty(board)
    if not find: return True
    row, col = find
    for num in range(1, 10):
        if is_valid(board, num, (row, col)):
            board[row][col] = num
            if solve(board): return True
            board[row][col] = 0
    return False

def generate_full_board():
    """Generates a fully solved Sudoku board."""
    board = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    def fill_board_randomly():
        find = find_empty(board)
        if not find: return True
        row, col = find
        nums = list(range(1, 10))
        random.shuffle(nums)
        for num in nums:
            if is_valid(board, num, (row, col)):
                board[row][col] = num
                if fill_board_randomly(): return True
                board[row][col] = 0
        return False
    fill_board_randomly()
    return board

def count_blanks(board):
    """Counts the number of empty cells (0) in the puzzle."""
    return sum(row.count(0) for row in board)

def create_puzzle(full_board, difficulty_level=40):
    """Removes a certain number of cells from the full board to create a puzzle."""
    puzzle = [row[:] for row in full_board]
    cells_to_remove = difficulty_level
    while cells_to_remove > 0:
        row, col = random.randint(0, 8), random.randint(0, 8)
        if puzzle[row][col] != 0:
            puzzle[row][col] = 0
            cells_to_remove -= 1
    return puzzle

#Pygame Grid Class
class Grid:
    def __init__(self, difficulty):
        self.full_board = generate_full_board()
        self.board = create_puzzle(self.full_board, difficulty)
        self.initial_board = [row[:] for row in self.board]
        self.user_answers = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.selected = None
        self.message = ""
        self.game_over = False
        self.total_blanks = count_blanks(self.initial_board)
        self.correct_count = 0
        self.hint_mask = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.wrong_attempts = 0

    def draw_grid(self, screen):
        """Draws the Sudoku grid lines."""
        for i in range(GRID_SIZE + 1):
            thickness = 3 if i % 3 == 0 else 1
            # Draw grid lines over the dark background
            pygame.draw.line(screen, WHITE, (0, i * SQUARE_SIZE), (WIDTH, i * SQUARE_SIZE), thickness)
            pygame.draw.line(screen, WHITE, (i * SQUARE_SIZE, 0), (i * SQUARE_SIZE, WIDTH), thickness)

    def draw_numbers(self, screen, FONT, RED, HINT_COLOR, BLACK):
        """Draws initial numbers and user-entered numbers, coloring incorrect attempts red."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x = c * SQUARE_SIZE
                y = r * SQUARE_SIZE

                if self.initial_board[r][c] != 0:
                    # Initial numbers white for contrast
                    text_surface = FONT.render(str(self.initial_board[r][c]), True, WHITE)
                    screen.blit(text_surface, (x + (SQUARE_SIZE - text_surface.get_width()) // 2,
                                                y + (SQUARE_SIZE - text_surface.get_height()) // 2))

                elif self.user_answers[r][c] != 0:
                    num = self.user_answers[r][c]
                    color = HINT_COLOR
                    
                    # Check for incorrect placement only if game is not over
                    if not self.game_over and num != self.full_board[r][c]:
                        color = RED

                    text_surface = FONT.render(str(num), True, color)
                    screen.blit(text_surface, (x + (SQUARE_SIZE - text_surface.get_width()) // 2,
                                                y + (SQUARE_SIZE - text_surface.get_height()) // 2))

    def draw_selection(self, screen, BLUE):
        """Draws the highlight rectangle around the selected cell."""
        if self.selected:
            r, c = self.selected
            x = c * SQUARE_SIZE
            y = r * SQUARE_SIZE
            pygame.draw.rect(screen, BLUE, (x, y, SQUARE_SIZE, SQUARE_SIZE), 3)

    def select(self, pos):
        """Sets the selected cell based on mouse click position."""
        if pos[1] > WIDTH:
            self.selected = None
            return
        col = pos[0] // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE
        if self.initial_board[row][col] == 0:
            self.selected = (row, col)
        else:
            self.selected = None

    def place_number(self, val):
        """Places a number in the selected cell and checks for correctness/game over condition."""
        if self.selected is None or self.game_over: return False
        r, c = self.selected
        
        # Check if the cell was already correctly solved by the user (to avoid double counting)
        was_correct = (self.user_answers[r][c] == self.full_board[r][c]) and (self.user_answers[r][c] != 0)

        self.hint_mask[r][c] = 0 # Not a hint if the user enters it
        self.user_answers[r][c] = val
        
        if val != self.full_board[r][c]:
            # Only increment wrong attempts if it was previously empty or wrong, and the new value is wrong
            if not was_correct:
                self.wrong_attempts += 1
            
            if self.wrong_attempts >= MAX_WRONG:
                self.message = f"Oops! Too many wrong attempts ({self.wrong_attempts}/{MAX_WRONG})!"
                self.game_over = True
            else:
                self.message = f"Wrong attempt {self.wrong_attempts}/{MAX_WRONG}"
            return True
            
        self.message = ""
        self.check_completion()
        return True

    def delete_number(self):
        """Clears the number in the selected cell."""
        if self.selected and not self.game_over:
            r, c = self.selected
            self.user_answers[r][c] = 0
            self.hint_mask[r][c] = 0
            self.check_completion()

    def calculate_correct_count(self):
        """Calculates how many user-entered (non-initial) cells match the solution."""
        count = 0
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                user_val = self.user_answers[r][c]
                if user_val != 0 and self.initial_board[r][c] == 0:
                    if user_val == self.full_board[r][c]:
                        count += 1
        return count

    def check_completion(self):
        """Checks if the puzzle is fully and correctly solved."""
        self.correct_count = self.calculate_correct_count()
        
        # Check if the whole board is filled (initial + user answers)
        is_filled = all(self.initial_board[r][c] != 0 or self.user_answers[r][c] != 0
                       for r in range(GRID_SIZE) for c in range(GRID_SIZE))

        if is_filled:
            # The puzzle is considered solved if the number of correct user answers
            # equals the total number of blanks.
            if self.correct_count == self.total_blanks:
                self.message = "SOLVED! Press 'R' for a new game."
                self.game_over = True
            else:
                self.message = "Board filled, but errors remain."
                self.game_over = False
                
        elif self.correct_count < self.total_blanks:
            self.message = f"Keep going! ({self.correct_count}/{self.total_blanks})"
            self.game_over = False
        else:
            self.message = ""

    def hint(self):
        """Fills the selected cell with the correct answer (using a hint)."""
        if self.selected and not self.game_over:
            r, c = self.selected
            if self.initial_board[r][c] == 0 and self.user_answers[r][c] != self.full_board[r][c]:
                self.user_answers[r][c] = self.full_board[r][c]
                self.hint_mask[r][c] = 1 # Mark as hint used
                self.check_completion()
                self.message = f"Hint used. ({self.correct_count}/{self.total_blanks})"
                return True
        return False

    def solve_board(self):
        """Fills the entire board with the solution."""
        if not self.game_over:
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if self.initial_board[r][c] == 0:
                        self.user_answers[r][c] = self.full_board[r][c]
                        self.hint_mask[r][c] = 1
            self.correct_count = self.total_blanks # Force correct count
            self.message = "Board solved by computer. Press R for a new game."
            self.game_over = True


def draw_info_panel(screen, grid, FONT_PG, SMALL_FONT_PG):
    """
    Draws the instruction, message, and score panel at the bottom.
    """
    panel_y = WIDTH
    panel_height = HEIGHT - WIDTH
    pygame.draw.rect(screen, GRAY, (0, panel_y, WIDTH, panel_height))

    #Line 1: Score and Help
    score_text = "Correct: {}/{}".format(grid.correct_count, grid.total_blanks)
    score_surface = SMALL_FONT_PG.render(score_text, True, BLACK)
    line1_y = panel_y + 4
    screen.blit(score_surface, (10, line1_y))

    help_text = "H: Hint | R: New Game | S: Solve"
    help_surface = SMALL_FONT_PG.render(help_text, True, BLACK)
    screen.blit(help_surface, (WIDTH - help_surface.get_width() - 10, line1_y))
    
    #Line 2: Attempts (Shifted down)
    attempts_text = f"Attempts: {grid.wrong_attempts}/{MAX_WRONG}"
    attempts_surface = SMALL_FONT_PG.render(attempts_text, True, BLACK)
    line2_y = panel_y + 20
    screen.blit(attempts_surface, (10, line2_y))


    #Line 3: Message/Instructions
    message_text = grid.message
    if not message_text and not grid.game_over:
        message_text = "Click a cell, enter 1-9. DEL/BACKSPACE to clear."

    text_surface = SMALL_FONT_PG.render(message_text, True, BLACK)
    text_x = (WIDTH - text_surface.get_width()) // 2
    line3_y = panel_y + 40
    text_y = line3_y - (text_surface.get_height() // 2)

    screen.blit(text_surface, (text_x, text_y))


def sudoku_main(tk_root):
    """
    The main Sudoku game loop. It hides Tkinter, runs Pygame, and restores Tkinter on exit.
    Includes a 15-second delay after a successful solve.
    """
    #Pygame Setup
    pygame.init()
    SCREEN=pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SUDO-GEN: Sudoku Generator & Checker")
    FONT_PG=pygame.font.SysFont("Inter", 40)
    SMALL_FONT_PG=pygame.font.SysFont("Times New Roman", 16)
    CLOCK=pygame.time.Clock()

    current_grid = Grid(difficulty=40)
    running = True
    game_result_message = "Game exited."
    
    # Delay closing sudoku screen
    delay_start_time = 0 
    SOLVE_DELAY_MS = 15000 # 15 seconds delay for successful solve

    # Hide Tkinter root window
    tk_root.withdraw()

    while running:
        
        # --- Check for Delay Completion (Runs every frame) ---
        if delay_start_time > 0:
            elapsed_time = pygame.time.get_ticks() - delay_start_time
            if elapsed_time >= SOLVE_DELAY_MS:
                running = False
                break
            # Update the message to show the countdown
            remaining = (SOLVE_DELAY_MS - elapsed_time) / 1000.0
            current_grid.message = f"SOLVED! Closing in {remaining:.1f}s..."


        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            # 'R' (New Game) is always allowed, even when game is over
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                current_grid = Grid(difficulty=40)
                delay_start_time = 0 # Reset delay state
                continue
            
            # Input is only processed if the game is NOT over and NOT in the delay phase
            if not current_grid.game_over and delay_start_time == 0:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    current_grid.select(pos)
                    current_grid.check_completion()

                if event.type == pygame.KEYDOWN:
                    val = 0
                    if event.key == pygame.K_1: val = 1
                    elif event.key == pygame.K_2: val = 2
                    elif event.key == pygame.K_3: val = 3
                    elif event.key == pygame.K_4: val = 4
                    elif event.key == pygame.K_5: val = 5
                    elif event.key == pygame.K_6: val = 6
                    elif event.key == pygame.K_7: val = 7
                    elif event.key == pygame.K_8: val = 8
                    elif event.key == pygame.K_9: val = 9

                    if val != 0:
                        current_grid.place_number(val)
                    elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                        current_grid.delete_number()
                    elif event.key == pygame.K_h:
                        current_grid.hint()
                    elif event.key == pygame.K_s:
                        current_grid.solve_board()
                    
        
        # --- Game Over State Transition ---
        # If the grid is now solved (and not already in delay mode):
        if current_grid.game_over and delay_start_time == 0:
            if current_grid.correct_count == current_grid.total_blanks and current_grid.wrong_attempts < MAX_WRONG:
                game_result_message = "Sudoku completed! 🎉"
                # Start the 15 second delay for a successful solve
                delay_start_time = pygame.time.get_ticks()
            else:
                # Game over from too many wrong attempts or manual solve (no delay needed)
                game_result_message = "Game Over. " + current_grid.message
                running = False
                break

        # --- Drawing ---
        SCREEN.fill(LIGHT_PURPLE)
        
        current_grid.draw_selection(SCREEN, BLUE)
        current_grid.draw_numbers(SCREEN, FONT_PG, RED, HINT_COLOR, BLACK)
        current_grid.draw_grid(SCREEN)
        draw_info_panel(SCREEN, current_grid, FONT_PG, SMALL_FONT_PG)

        pygame.display.flip()
        CLOCK.tick(FPS)

    # 2. Pygame Shutdown and Tkinter Restore
    pygame.quit()
    
    # Show completion messagebox
    messagebox.showinfo("Sudoku Session Complete", game_result_message)
    
    # Restore the Tkinter window
    tk_root.deiconify()


def start_game_sudoku(tk_home_window):
    """Bridge function: hides Tkinter window and starts the Sudoku game."""
    tk_home_window.withdraw() # Hide the Tkinter window
    sudoku_main(tk_home_window)


# --- Tkinter UI Logic ---

# root (Login Window)
root = Tk()
root.title('SUDO-GEN - User Login')
root.geometry("1050x603")

# --- Database Connection Setup ---
try:
    con = sqlcon.connect(host = "localhost", user = "root", passwd = "sql123", collation="utf8mb4_unicode_ci", charset="utf8mb4")
    myc = con.cursor()
    myc.execute("use planner")
    db_connected = True
except sqlcon.Error as e:
    messagebox.showerror("Database Error", f"Could not connect to database or select 'planner'. Login/Account features will be disabled. Error: {e}")
    db_connected = False


# Login Frame Setup
try:
    bg=PhotoImage(file ='login (1).png')
except TclError:
    bg = PhotoImage(width=1, height=1)
    root.configure(bg='purple4')
    
canvas_login=Canvas(root,width=800,height=800)
canvas_login.pack(fill='both',expand=True)
canvas_login.create_image(0,0,image=bg,anchor='nw')


login = Frame(root,height = 700 , width = 500)
login.configure(bg='purple4')

wel = Label(login, text = "     WELCOME TO SUDO-GEN     ",foreground='white')
wel.configure(bg='purple4')
wel.config(font=('TimesNewRoman',13,))
wel.pack(pady=10)

lu = Label(login, text = "Enter Username", bg='purple4', foreground='white', font=('TimesNewRoman',10))
lu.pack()

usr= Entry(login, font=('TimesNewRoman',10))
usr.pack()

lp = Label(login, text = "Enter Password", bg='purple4', foreground='white', font=('TimesNewRoman',10))
lp.pack()

pas = Entry(login,show = "*")
pas.pack()


def logout(tk_window):
    """Destroys the current window and brings back the login screen."""
    tk_window.destroy()
    root.deiconify()

def sudoku_launch_page(u):
    """
    The new post-login home page.
    """
    # Use Toplevel to create a new window
    sudoku_home = Toplevel(root)
    sudoku_home.title('SUDO-GEN - Launch Pad')
    sudoku_home.geometry('500x400')
    # Swapped purple3 to purple4 -> purple4 to purple3
    sudoku_home.configure(bg='purple4')
    root.withdraw() # Hide the main login window

    # Menubar setup
    menubar = Menu(sudoku_home)
    sudoku_home.config(menu=menubar)
    
    # Game Menu
    game_menu = Menu(menubar, tearoff=0)
    game_menu.add_command(label='🚀 Launch Sudoku', command=lambda: start_game_sudoku(sudoku_home))
    menubar.add_cascade(label='🔢 Game', menu=game_menu)
    
    # Account Menu
    acc_menu = Menu(menubar, tearoff=0)
    acc_menu.add_command(label=f'👤 Logged in as: {u}', command=None)
    acc_menu.add_command(label='🔑 Logout', command=lambda: logout(sudoku_home))
    menubar.add_cascade(label='👤 User', menu=acc_menu)
    
    menubar.add_command(label='❌ Exit', command=root.destroy)


    # Center Frame for the button
    center_frame = Frame(sudoku_home, bg='purple4', padx=20, pady=20)
    center_frame.pack(expand=True, fill=BOTH)

    wel = Label(center_frame, text = f"Welcome, {u}!\nReady to generate and solve Sudoku?", foreground='white')
    # Swapped purple3 to purple4 -> purple4 to purple3
    wel.configure(bg='purple4')
    wel.config(font=('Times New Roman',18,'bold'), justify=CENTER)
    wel.pack(pady=30)

    # The main button to launch Pygame
    start_btn = Button(center_frame,
                        text="START SUDOKU",
                        command=lambda: start_game_sudoku(sudoku_home),
                        fg='white',
                        bg='purple3',
                        activebackground='purple',
                        activeforeground='white',
                        font=('Times New Roman', 12, 'bold'),
                        width=15,
                        height=1)
    start_btn.pack(pady=20)


def homeopen():
    """Handles login and redirects to the Sudoku launch page on success."""
    if not db_connected:
        messagebox.showerror("Feature Disabled", "Database is not connected. Cannot log in.")
        return

    myc.execute("select * from login")
    k = myc.fetchall()
    u = usr.get()
    p = pas.get()
    
    login_successful = False
    for i in k:
        if u in i and p in i:
            login_successful = True
            break

    if login_successful:
        messagebox.showinfo("LOGIN SUCCESSFUL",'Login Successful')
        # Clear fields
        usr.delete(0, END)
        pas.delete(0, END)
        sudoku_launch_page(u) # Go to the new minimalist home page
    else:
        messagebox.showinfo('LOGIN FAILED','Login Failed: Invalid credentials')


enter = Button(login, text = "Enter",command = homeopen, fg='black')
enter.pack(pady=10)

# New Account Page
def cracc(prev_window=None):
    if not db_connected:
        messagebox.showerror("Feature Disabled", "Database is not connected. Cannot create account.")
        return
    
    if prev_window:
        prev_window.withdraw()
    root.withdraw()
    
    cre=Tk()
    cre.geometry('400x400')
    cre.title('SUDO-GEN - Create Account')
    # Swapped purple3 to purple4 -> purple4 to purple3
    cre.config(bg='purple4')

    creacnt = Frame(cre,height = 300 , width = 300 , bd=2, relief=SOLID, highlightthickness=2, highlightbackground="white")
    # Swapped purple3 to purple4 -> purple4 to purple3
    creacnt.configure(bg='purple4')

    spcre= Label(creacnt, text = "SUDO-GEN Account Creation", foreground='white')
    # Swapped purple3 to purple4 -> purple4 to purple3
    spcre.configure(bg='purple4')
    spcre.config(font=('TimesNewRoman',13, 'bold'))
    spcre.pack(pady=10)

    h= Label(creacnt, text = "Create Username", bg='purple4', foreground='white', font=('TimesNewRoman',10))
    h.pack()
    h_entry= Entry(creacnt,font=('TimesNewRoman',10))
    h_entry.pack()

    p= Label(creacnt, text = "Create Password", bg='purple4', foreground='white', font=('TimesNewRoman',10))
    p.pack()
    p_entry = Entry(creacnt,show = "*")
    p_entry.pack()

    cp=Label(creacnt, text='Confirm Password', bg='purple4', foreground='white', font=('TimesNewRoman',10))
    cp.pack()
    cp_entry=Entry(creacnt, show='*')
    cp_entry.pack()

    cresp=Label(creacnt, text = ' ', foreground='purple4', bg='purple4')
    cresp.pack(pady=5)
    
    def create_account():
        user = h_entry.get()
        paswod = p_entry.get()
        cpaswod = cp_entry.get()
        if not user or not paswod:
             messagebox.showerror('ACCOUNT FAILED',"Username and Password cannot be empty.")
             return
             
        if cpaswod == paswod:
                myc.execute("select * from login")
                data=myc.fetchall()
                flag=True
                for i in data:
                    if i[0]==user:
                            flag=False
                            break
                if flag:
                    try:
                        myc.execute("insert into login values(%s,%s)",(user , paswod))
                        con.commit()
                        messagebox.showinfo("ACCOUNT CREATED","Account has been created")
                        cre.destroy()
                        if prev_window:
                            prev_window.deiconify() # Restore home window if came from there
                        else:
                            root.deiconify() # Restore login window
                    except sqlcon.Error as err:
                        messagebox.showerror("Database Error", f"Failed to insert user: {err}")
                        cre.destroy()
                        root.deiconify()
                else:
                    messagebox.showerror('USERNAME TAKEN',"Please enter another username")
            
        else:
            messagebox.showerror('ACCOUNT FAILED',"Passwords don't match")
            
    sub_cre=Button(creacnt, text='CREATE ACCOUNT', command=create_account, fg='black')
    sub_cre.pack(pady=5)
    
    def cr_back():
        cre.destroy()
        if prev_window:
            prev_window.deiconify()
        else:
            root.deiconify()
        
    creback=Button(creacnt, text='BACK TO LOGIN PAGE', command=cr_back, fg='black')
    creback.pack(pady=5)
    creacnt.place(relx= 0.5, rely = 0.5, anchor = CENTER)
    
    cre.mainloop()

crac=Button(login, text='Create Account', command=lambda: cracc(None), fg='black')
crac.pack(pady=10)
login.place(relx = 0.5,rely = 0.5 , anchor = CENTER)

root.mainloop()
