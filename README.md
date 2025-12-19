# SUDO-GEN

SUDO-GEN is a Python application that provides a Sudoku generator and interactive Sudoku game with a Tkinter login/launcher and a Pygame-based game screen. It includes optional MySQL-backed user accounts for login and account creation.

## Features
- Generate a full Sudoku board and create puzzles.
- Interactive Pygame-based Sudoku UI with hints, solve, and wrong-attempt limit.
- Tkinter login screen and a launch page for starting games.
- Optional MySQL integration for account creation and login.

## Requirements
- Python 3.8+
- pygame
- tkinter (usually included with Python)
- mysql-connector-python (if using the DB features)
- A MySQL database named `planner` with a `login` table (if you want account features).

## Installation
1. Install dependencies:

   pip install pygame mysql-connector-python

2. Configure MySQL (optional):
   - Create a database named `planner`
   - Create a `login` table with at least two columns for username and password

## Usage
1. Run the Tkinter launcher: `python "tkinter integration.py"` to open the login screen.
2. Create an account (optional) or log in.
3. Use the launch page to start the Pygame Sudoku game.

## Notes / Security
- The current login implementation stores passwords in plaintext in the database. For production use, store password hashes (bcrypt/argon2) and use environment variables or a configuration file for DB credentials.
- The script assumes a MySQL server running locally with user `root` and password `sql123`; change these before deploying.
