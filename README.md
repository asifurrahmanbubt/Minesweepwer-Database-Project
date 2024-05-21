# Minesweeper Database Project

This project is a web-based Minesweeper game integrated with a MySQL database for user management, game state saving, and statistics tracking. It was developed as part of the CSE-208 Database Lab Course.

## Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Usage](#usage)
- [File Structure](#file-structure)
- [License](#license)

## Features

- User Registration and Login
- Save and Load Game States
- Track User Statistics
- Different Difficulty Levels
- Customizable Grid Sizes

## Technologies Used

- Python
- MySQL
- XAMPP (for MySQL database)
- Tkinter (for GUI)
- PIL (for image handling)
- ttkthemes (for themed Tkinter widgets)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/Minesweeper-Database-Project.git
    ```
2. Navigate to the project directory:
    ```bash
    cd Minesweeper-Database-Project
    ```
3. Set up your Python environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

## Database Setup

1. Ensure you have XAMPP installed and running.
2. Open the XAMPP Control Panel and start the MySQL module.
3. Import the `minesweeper_db.sql` file into your MySQL server to create the database and necessary tables:
    ```sql
    mysql -u root -p minesweeper_db < /path/to/minesweeper_db.sql
    ```

## Usage

1. Start the application by running:
    ```bash
    python main.py
    ```
2. Register a new user or log in with an existing account.
3. Select the desired difficulty level or customize your game.
4. Play the game and your progress will be saved to the database.

## File Structure

- `main.py`: Contains the main game logic and GUI setup.
- `database.py`: Contains functions for database connection, user registration, login, game state saving, and statistics fetching.
- `minesweeper_db.sql`: SQL script for setting up the MySQL database.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
