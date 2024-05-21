from tkinter import *
import tkinter.ttk as ttk
from ttkthemes import ThemedTk
from tkinter.font import Font
from tkinter import messagebox
from PIL import ImageTk, Image
from functools import partial
import random
import time
import math
import os
import base64
import threading

from database import create_db_connection, register_user, save_game_state, load_game_settings, get_user_id, validate_user, fetch_user_statistics

class Counter(object):
    def __init__(self):
        self.sec_block = [
            [1, 1, 1, 0, 1, 1, 1],
            [0, 0, 1, 0, 0, 1, 0],
            [1, 0, 1, 1, 1, 0, 1],
            [1, 0, 1, 1, 0, 1, 1],
            [0, 1, 1, 1, 0, 1, 0],
            [1, 1, 0, 1, 0, 1, 1],
            [1, 1, 0, 1, 1, 1, 1],
            [1, 0, 1, 0, 0, 1, 0],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 0, 1, 1]
        ]

    def draw(self, canvas, sec):
        canvas.create_polygon(3, 2, 11, 2, 9, 4, 5, 4, outline='red' if self.sec_block[sec][0] else 'black',
                              fill='red' if self.sec_block[sec][0] else 'black')
        canvas.create_polygon(2, 3, 2, 11, 4, 9, 4, 5, outline='red' if self.sec_block[sec][1] else 'black',
                              fill='red' if self.sec_block[sec][1] else 'black')
        canvas.create_polygon(12, 3, 12, 11, 10, 9, 10, 5, outline='red' if self.sec_block[sec][2] else 'black',
                              fill='red' if self.sec_block[sec][2] else 'black')
        canvas.create_polygon(3, 12, 5, 11, 9, 11, 11, 12, 10, 13, 4, 13,
                              outline='red' if self.sec_block[sec][3] else 'black',
                              fill='red' if self.sec_block[sec][3] else 'black')
        canvas.create_polygon(2, 13, 2, 21, 4, 19, 4, 15, outline='red' if self.sec_block[sec][4] else 'black',
                              fill='red' if self.sec_block[sec][4] else 'black')
        canvas.create_polygon(12, 13, 12, 21, 10, 19, 10, 15, outline='red' if self.sec_block[sec][5] else 'black',
                              fill='red' if self.sec_block[sec][5] else 'black')
        canvas.create_polygon(9, 20, 5, 20, 3, 22, 11, 22, outline='red' if self.sec_block[sec][6] else 'black',
                              fill='red' if self.sec_block[sec][6] else 'black')

class MineSweeper(object):
    def __init__(self, root, difficulty=0):
        self.difficulty_data = [(9, 9, 10), (16, 16, 40), (30, 16, 99)]
        self.difficulty = difficulty
        self.width, self.height, self.total_mine = self.difficulty_data[self.difficulty]
        self.root = root
        self.root.config(bg='#C0C0C0')
        self.root.geometry('{}x{}'.format(self.width * 20 + 24, self.height * 20 + 73))
        self.root.resizable(False, False)
        self.is_developer = False
        self.current_dev_pass = None
        self.color = ['#0100FE', '#017F01', '#FE0000', '#010080', '#810102', '#008081', '#000000', '#808080']
        self.unvisited = sum([[(height, width) for width in range(self.width)] for height in range(self.height)], [])
        self.grid = [[0 for j in range(self.width)] for i in range(self.height)]
        self.visited = []
        self.block = []
        self.marked = []
        self.bombed = []
        self.current_time = '000'
        self.bomb_left = str(self.total_mine).zfill(3)
        self.first = True
        self.timer = Counter()
        self.bomb_left_counter = Counter()
        self.timer_start = False
        self.nav_bar_dif_val = IntVar()
        self.nav_bar_dif_val.set(self.difficulty)
        self.bomb = PhotoImage(file='asset/bomb.png')
        self.flag = PhotoImage(file='asset/flag.png')
        self.smile, self.shock, self.cool, self.died = [PhotoImage(file='asset/{}.png'.format(i)) for i in range(1, 5)]
        self.neighbour = lambda x, y: [(y, x) for y, x in
                                       [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1), (y + 1, x + 1), (y - 1, x - 1),
                                        (y + 1, x - 1), (y - 1, x + 1)] if 0 <= y < self.height and 0 <= x < self.width]
        self.lose = lambda x, y: bool(self.grid[y][x])
        if not os.path.exists('minesweeper_record.dat'):
            self.record = [[999, 'Anonymous'], [999, 'Anonymous'], [999, 'Anonymous']]
            with open('minesweeper_record.dat', 'wb') as record_file:
                record_file.write(base64.b64encode(str(self.record).encode('utf-8')))
        else:
            self.record = eval(base64.b64decode(open('minesweeper_record.dat', 'r').read()))
        self.navbar = Menu(self.root)
        self.root.config(menu=self.navbar)
        self.game_menu = Menu(self.navbar, tearoff=0)
        self.navbar.add_cascade(label="Game", menu=self.game_menu)
        self.game_menu.add_command(label="New                     F2",
                                   command=lambda: self.cleanup(difficulty=self.difficulty))
        self.game_menu.add_separator()
        self.game_menu.add_radiobutton(label='Beginner', variable=self.nav_bar_dif_val, value=0,
                                       command=lambda: self.cleanup(difficulty=0))
        self.game_menu.add_radiobutton(label='Intermidiate', variable=self.nav_bar_dif_val, value=1,
                                       command=lambda: self.cleanup(difficulty=1))
        self.game_menu.add_radiobutton(label='Expert', variable=self.nav_bar_dif_val, value=2,
                                       command=lambda: self.cleanup(difficulty=2))
        self.game_menu.add_radiobutton(label='Custom...', variable=self.nav_bar_dif_val, value=3,
                                       command=self.custom_game)
        self.game_menu.add_separator()
        self.game_menu.add_command(label="Best Times...", command=self.show_record)
        self.game_menu.add_command(label="Statistics...", command=self.show_statistics)
        self.game_menu.add_separator()
        self.game_menu.add_command(label="Save Game", command=self.save_state)
        self.game_menu.add_command(label="Load Game", command=self.load_settings)
        self.game_menu.add_command(label="Exit", command=self.root.quit)
        self.grid_border = Label(self.root, relief=SUNKEN, bd=3, bg='#C0C0C0')
        self.top_container_frame = Frame(self.root, relief=SUNKEN, bd=3, bg='#C0C0C0')
        self.top_container = Frame(self.root, relief=FLAT, bg='#C0C0C0')
        self.timer_container = Frame(self.top_container, relief=SUNKEN, bd=1)
        self.bomb_left_counter_container = Frame(self.top_container, relief=SUNKEN, bd=1)
        self.face_button = Button(self.top_container, image=self.smile, relief=RAISED, bd=3, bg='#C0C0C0',
                                  command=lambda: self.cleanup(difficulty=self.difficulty))
        self.timer_block1 = Canvas(self.timer_container, width=15, height=25, bg='black', highlightbackground='black',
                                   highlightthickness=0)
        self.timer_block2 = Canvas(self.timer_container, width=15, height=25, bg='black', highlightbackground='black',
                                   highlightthickness=0)
        self.timer_block3 = Canvas(self.timer_container, width=15, height=25, bg='black', highlightbackground='black',
                                   highlightthickness=0)
        self.bomb_left_block1 = Canvas(self.bomb_left_counter_container, width=15, height=25, bg='black',
                                       highlightbackground='black', highlightthickness=0)
        self.bomb_left_block2 = Canvas(self.bomb_left_counter_container, width=15, height=25, bg='black',
                                       highlightbackground='black', highlightthickness=0)
        self.bomb_left_block3 = Canvas(self.bomb_left_counter_container, width=15, height=25, bg='black',
                                       highlightbackground='black', highlightthickness=0)
        self.timer.draw(self.timer_block1, 0)
        self.timer.draw(self.timer_block2, 0)
        self.timer.draw(self.timer_block3, 0)
        self.bomb_left_counter.draw(self.bomb_left_block1, int(self.bomb_left[0]))
        self.bomb_left_counter.draw(self.bomb_left_block2, int(self.bomb_left[1]))
        self.bomb_left_counter.draw(self.bomb_left_block3, int(self.bomb_left[2]))
        self.root.bind('<F2>', lambda e: self.cleanup(e, difficulty=self.difficulty))
        self.root.bind('<Control-Alt-d><Control-Alt-v>', self.developer_verify)
        self.root.bind('<Control-Alt-d><Control-Alt-r>', self.developer_register)
        self.root.bind('<Control-Alt-d><Control-Alt-c>', self.developer_create)

        # Database-related attributes
        self.connection = create_db_connection()
        self.username = None
        self.user_id = None

        # Add Registration and Login Buttons
        self.add_login_registration_buttons()

    def add_login_registration_buttons(self):
        button_frame = Frame(self.root, bg='#C0C0C0')
        button_frame.pack(expand=True)

        self.login_button = Button(button_frame, text="Login", command=self.login_user)
        self.register_button = Button(button_frame, text="Register", command=self.register_user)
        self.login_button.pack(side=LEFT, padx=10, pady=10)
        self.register_button.pack(side=LEFT, padx=10, pady=10)

    def register_user(self):
        def submit_registration():
            username = username_entry.get()
            password = password_entry.get()
            email = email_entry.get()
            self.register(username, password, email)
            registration_window.destroy()

        registration_window = Toplevel(self.root)
        registration_window.title("Register User")
        Label(registration_window, text="Username:").grid(row=0, column=0)
        username_entry = Entry(registration_window, width=30)
        username_entry.grid(row=0, column=1)
        Label(registration_window, text="Password:").grid(row=1, column=0)
        password_entry = Entry(registration_window, show='*', width=30)
        password_entry.grid(row=1, column=1)
        Label(registration_window, text="Email:").grid(row=2, column=0)
        email_entry = Entry(registration_window, width=30)
        email_entry.grid(row=2, column=1)
        Button(registration_window, text="Register", command=submit_registration).grid(row=3, columnspan=2)

    def login_user(self):
        def submit_login():
            username = username_entry.get()
            password = password_entry.get()
            if not username or not password:
                messagebox.showerror("Login Error", "Both username and password are required")
                return
            if validate_user(self.connection, username, password):
                self.username = username
                self.user_id = get_user_id(self.connection, username)
                if self.user_id:
                    self.load_settings()
                    login_window.destroy()
                    self.cleanup()
                    self.play()
            else:
                messagebox.showerror("Login Error", "Invalid username or password")

        login_window = Toplevel(self.root)
        login_window.title("Login User")
        Label(login_window, text="Username:").grid(row=0, column=0)
        username_entry = Entry(login_window, width=30)
        username_entry.grid(row=0, column=1)
        Label(login_window, text="Password:").grid(row=1, column=0)
        password_entry = Entry(login_window, show='*', width=30)
        password_entry.grid(row=1, column=1)
        Button(login_window, text="Login", command=submit_login).grid(row=2, columnspan=2)

    def developer_register(self, e):
        self.current_dev_pass = secrets.token_hex(nbytes=64)

        mail.ehlo()
        mail.starttls()
        message = MIMEMultipart("alternative")
        message["Subject"] = "Minesweeper Registration Code"
        message.attach(MIMEText(
            r"<html> <body> <p>Hi,<br> This is your Minesweeper registration code:</p> <br/> <strong>" + self.current_dev_pass + "</strong> </body> </html> ",
            "html"))

        mail.close()

        messagebox.showwarning('Registration Code Sent',
                               'Registration code has been sent to your mail box.\nGo and check it out!')

    def developer_create(self, e):
        dev_code_verify_win = ThemedTk(theme='breeze')

        registration_code_label = ttk.Label(dev_code_verify_win, text='Enter registration code:')
        registration_code_input = ttk.Entry(dev_code_verify_win, width=64)
        registration_proceed_btn = ttk.Button(dev_code_verify_win, text='Register')

        registration_code_label.grid(row=0, column=0, padx=10, pady=10, sticky=W)
        registration_code_input.grid(row=1, column=0, padx=10, pady=(0, 10))

        dev_code_verify_win.mainloop()

    def developer_verify(self, e):
        dev_verify_win = ThemedTk(theme='breeze')
        dev_verify_win.resizable(False, False)
        dev_verify_win.title('Dev Login')

        dev_key_label = ttk.Label(dev_verify_win, text='Dev Key:')
        dev_pass_label = ttk.Label(dev_verify_win, text='Password:')

        dev_key_input = ttk.Entry(dev_verify_win, width=30)
        dev_pass_input = ttk.Entry(dev_verify_win, show='\u25CF', width=30)

        cancel_button = ttk.Button(dev_verify_win, text='Cancel', command=dev_verify_win.destroy)
        OK_button = ttk.Button(dev_verify_win, text='OK',
                               command=lambda: self.dev_verify_second(dev_key_input.get(), dev_pass_input.get(),
                                                                      dev_verify_win))

        dev_key_label.grid(row=0, column=0, padx=10, pady=(10, 0))
        dev_pass_label.grid(row=1, column=0, padx=10, pady=(5, 10))

        dev_key_input.grid(row=0, column=1, columnspan=2, padx=10, pady=(10, 0))
        dev_pass_input.grid(row=1, column=1, columnspan=2, padx=10, pady=(5, 10))

        cancel_button.grid(row=2, column=1, sticky=E, pady=(0, 10))
        OK_button.grid(row=2, column=2, sticky=E, pady=(0, 10), padx=(0, 10))

        dev_verify_win.mainloop()

    def dev_verify_second(self, key, pass_, win):
        win.destroy()
        print(key, pass_)

    def unbind_all(self, current_y, current_x):
        self.block[current_y][current_x].unbind('<Button-3>')
        self.block[current_y][current_x].unbind('<ButtonPress-1>')
        self.block[current_y][current_x].unbind('<ButtonRelease-1>')

    def check_grid(self, current_y, current_x, recur=False):
        if self.first:
            self.bomb_coor = random.sample(sum([[(y, x) for x in range(self.width) if
                                                 (y, x) not in self.neighbour(current_x, current_y) + [
                                                     (current_y, current_x)]] for y in range(self.height)], []),
                                           self.total_mine)
            for y, x in self.bomb_coor: self.grid[y][x] = 1
            self.run_time = time.time()
            self.timer_start = True
            threading.Thread(target=self.start_timer).start()
        self.first = False

        if self.lose(current_x, current_y) and not recur:
            self.timer_start = False
            for y in range(len(self.block)):
                for x in range(len(self.block[0])):
                    self.block[y][x].config(state=DISABLED,
                                            text='' if self.grid[y][x] else self.block[y][x].cget('text'),
                                            disabledforeground='black' if self.grid[y][x] else self.block[y][x][
                                                'disabledforeground'])
                    self.bombed.append(Label(self.root, image=self.bomb, relief=RAISED, bd=3)) if self.grid[y][
                        x] else None
                    self.bombed[-1].place(x=13 + x * 20, y=63 + y * 20, width=20, height=20) if self.grid[y][
                        x] else None
                    self.unbind_all(y, x)
                    root.update()
            return

        self.bomb_count = len([1 for y, x in self.neighbour(current_x, current_y) if self.grid[y][x]])
        if self.bomb_count:
            self.block[current_y][current_x].config(state=DISABLED, text=str(self.bomb_count),
                                                    disabledforeground=self.color[self.bomb_count])
            root.update()
            self.visited.append((current_y, current_x))
            self.unvisited.remove((current_y, current_x))
            self.unbind_all(current_y, current_x)
        else:
            self.block[current_y][current_x].config(state=DISABLED, bg='#C0C0C0', relief=RIDGE, bd=1,
                                                    highlightbackground='#C0C0C0')
            root.update()
            self.visited.append((current_y, current_x))
            self.unvisited.remove((current_y, current_x))
            self.unbind_all(current_y, current_x)
            for cell_y, cell_x in self.neighbour(current_x, current_y):
                if not self.grid[current_y][current_x] and (cell_y, cell_x) not in self.visited and \
                        self.block[cell_y][cell_x]['text'] != 'O':
                    self.check_grid(cell_y, cell_x, recur=True)

        if sorted(self.unvisited) == sorted(self.bomb_coor):
            self.timer_start = False
            self.face_button.config(image=self.cool)
            self.bomb_left = '000'
            self.update_bomb_left()
            for y in range(len(self.block)):
                for x in range(len(self.block[0])):
                    self.block[y][x].config(command=0)
                    self.unbind_all(y, x)
            self.update_record()

    def update_record(self):
        if self.difficulty < 3 and self.record[self.difficulty][0] > int(self.current_time):
            self.record[self.difficulty][0] = int(self.current_time) - 1
            self.record[self.difficulty][1] = self.ask_record_name()
            with open('minesweeper_record.dat', 'wb') as record_file:
                record_file.write(base64.b64encode(str(self.record).encode('utf-8')))

    def mark_bomb(self, current_y, current_x, e):
        if self.block[current_y][current_x]['text'] != 'O':
            self.marked.append((current_y, current_x))
            self.block[current_y][current_x].config(text='O', image=self.flag, foreground='#000000', command=0)
            self.bomb_left = str(int(self.bomb_left) - 1).zfill(3) if int(self.bomb_left) - 1 >= 0 else '000'
            self.update_bomb_left()

        elif self.block[current_y][current_x]['text'] == 'O':
            self.marked.remove((current_y, current_x))
            self.temp_command = partial(self.check_grid, current_y, current_x)
            self.block[current_y][current_x].config(image='', text='', command=self.temp_command)
            self.bomb_left = str(int(self.bomb_left) + 1).zfill(3) if int(
                self.bomb_left) + 1 <= self.total_mine else str(self.total_mine).zfill(3)
            self.update_bomb_left()

    def change_face(self, current_y, current_x, e):
        if e.type == EventType.ButtonPress:
            self.face_button.config(image=self.shock)
        elif e.type == EventType.ButtonRelease:
            if self.grid[current_y][current_x] and (current_y, current_x) not in self.marked:
                self.face_button.config(image=self.died)
            else:
                self.face_button.config(image=self.smile)

    def update_bomb_left(self):
        self.bomb_left_block1.delete('all')
        self.bomb_left_block2.delete('all')
        self.bomb_left_block3.delete('all')
        self.bomb_left_counter.draw(self.bomb_left_block1, int(self.bomb_left[0]))
        self.bomb_left_counter.draw(self.bomb_left_block2, int(self.bomb_left[1]))
        self.bomb_left_counter.draw(self.bomb_left_block3, int(self.bomb_left[2]))

    def start_timer(self):
        if not self.timer_start: return
        self.timer_block1.delete('all')
        self.timer_block2.delete('all')
        self.timer_block3.delete('all')
        self.timer.draw(self.timer_block1, int(self.current_time[0]))
        self.timer.draw(self.timer_block2, int(self.current_time[1]))
        self.timer.draw(self.timer_block3, int(self.current_time[2]))
        self.current_time = str(math.ceil(time.time() - self.run_time)).zfill(3)
        self.root.after(1000, self.start_timer)
        self.timer_start = True

    def custom_game(self):

        def return_custom():
            self.width, self.height, self.total_mine = int(width_input.get()), int(height_input.get()), int(
                bomb_amount_input.get())
            custom_prompt.destroy()
            self.cleanup(difficulty=3)

        custom_prompt = ThemedTk(theme='breeze')
        custom_prompt.geometry('265x166')
        custom_prompt.title('Custom')
        custom_prompt.focus_force()

        height_label = ttk.Label(custom_prompt, text='Height:')
        width_label = ttk.Label(custom_prompt, text='Width:')
        bomb_amount_label = ttk.Label(custom_prompt, text='Mines:')

        width_input = ttk.Spinbox(custom_prompt, width=5, from_=9, to=24)
        height_input = ttk.Spinbox(custom_prompt, width=5, from_=9, to=30)
        bomb_amount_input = ttk.Spinbox(custom_prompt, width=5, from_=9, to=99)

        ok_button = ttk.Button(custom_prompt, text='OK', command=return_custom)
        cancel_button = ttk.Button(custom_prompt, text='Cancel', command=custom_prompt.destroy)

        height_label.grid(row=0, column=0, padx=15, pady=(30, 0))
        width_label.grid(row=1, column=0, padx=15, pady=(5, 0))
        bomb_amount_label.grid(row=2, column=0, padx=15, pady=(5, 0))

        height_input.grid(row=0, column=1, padx=15, pady=(30, 0))
        width_input.grid(row=1, column=1, padx=15, pady=(5, 0))
        bomb_amount_input.grid(row=2, column=1, padx=15, pady=(5, 0))

        ok_button.grid(row=0, column=2, pady=(30, 0))
        cancel_button.grid(row=2, column=2, pady=(5, 0))

        width_input.set(self.width)
        height_input.set(self.height)
        bomb_amount_input.set(self.total_mine)

        custom_prompt.mainloop()

    def cleanup(self, *args, difficulty=0):
        [i.place_forget() for i in self.bombed]
        self.width, self.height, self.total_mine = self.difficulty_data[difficulty] if difficulty != 3 else \
            (
                self.width if self.width <= 30 else 30,
                self.height if self.height <= 24 else 24,
                self.total_mine if self.total_mine <= 99 else 99
            )
        self.root.geometry('{}x{}'.format(self.width * 20 + 24, self.height * 20 + 73))
        self.unvisited = sum([[(y, x) for x in range(self.width)] for y in range(self.height)], [])
        self.visited = []
        self.marked = []
        self.bombed = []
        self.first = True
        self.grid = [[0 for x in range(self.width)] for y in range(self.height)]
        self.face_button.config(image=self.smile)
        self.timer_start = False
        self.current_time = '000'
        self.timer.draw(self.timer_block1, 0)
        self.timer.draw(self.timer_block2, 0)
        self.timer.draw(self.timer_block3, 0)
        self.bomb_left = str(self.total_mine).zfill(3)
        self.update_bomb_left()

        if difficulty == self.difficulty and self.difficulty != 3:
            for y in range(len(self.block)):
                for x in range(len(self.block[0])):
                    self.temp_command = partial(self.check_grid, y, x)
                    self.right_click_event = partial(self.mark_bomb, y, x)
                    self.change_face_event = partial(self.change_face, y, x)
                    self.block[y][x].config(command=self.temp_command, relief=RAISED, bd=3,
                                            font=Font(weight='bold', family='small fonts', size=7),
                                            bg='SystemButtonFace', state=NORMAL, text='', image='')
                    self.block[y][x].bind('<Button-3>', self.right_click_event)
                    self.block[y][x].bind('<ButtonPress-1>', self.change_face_event)
                    self.block[y][x].bind('<ButtonRelease-1>', self.change_face_event)
        else:
            self.difficulty = difficulty
            self.timer_container.place(x=self.width * 20 - 3.5, y=3.5, width=47, height=27, anchor=NE)
            self.face_button.place(x=(self.width * 20 + 2) // 2 - 2, y=17, anchor=CENTER, width=25, height=25)
            self.top_container_frame.place(x=10, y=10, width=self.width * 20 + 6, height=40)
            self.top_container.place(x=12, y=12, width=self.width * 20 + 2, height=36)
            self.grid_border.place(x=11, y=60, width=self.width * 20 + 4, height=self.height * 20 + 4)
            for y in range(len(self.block)):
                for x in range(len(self.block[y])):
                    self.block[y][x].place_forget()
            self.block.clear()
            for y in range(self.height):
                self.block.append([])
                for x in range(self.width):
                    self.temp_command = partial(self.check_grid, y, x)
                    self.right_click_event = partial(self.mark_bomb, y, x)
                    self.change_face_event = partial(self.change_face, y, x)
                    self.block[y].append(Button(self.root, command=self.temp_command, relief=RAISED, bd=3,
                                                font=Font(weight='bold', family='small fonts', size=7)))
                    self.block[y][x].bind('<Button-3>', self.right_click_event)
                    self.block[y][x].bind('<ButtonPress-1>', self.change_face_event)
                    self.block[y][x].bind('<ButtonRelease-1>', self.change_face_event)
            for y in range(len(self.block)):
                for x in range(len(self.block[y])):
                    self.block[y][x].place(x=13 + x * 20, y=62 + y * 20, width=20, height=20)
                    self.root.update()

    def ask_record_name(self):

        def return_name():
            global return_, name
            return_ = True
            name = ask_name_input.get()
            prompt_record_name.destroy()

        global return_
        return_ = False

        prompt_record_name = ThemedTk(theme='breeze')
        prompt_record_name.title('Fastest Time')

        ask_name_label = ttk.Label(prompt_record_name,
                                   text='You have the fastest time for Intermidiate level.\nPlease enter your name:',
                                   anchor=CENTER, justify=CENTER)
        ask_name_input = ttk.Entry(prompt_record_name)
        ok_button = ttk.Button(prompt_record_name, text='OK', command=return_name)

        ask_name_label.grid(row=0, column=0, padx=10, pady=10)
        ask_name_input.grid(row=1, column=0, padx=10)
        ok_button.grid(row=2, column=0, padx=10, pady=10)

        while not return_:
            try:
                prompt_record_name.update()
            except:
                pass
        return name

    def show_record(self):
        record_win = ThemedTk(theme='breeze')
        record_win.title('Game Record')
        record_win.geometry('292x106')
        record_win.focus_force()

        beginner_label = Label(record_win, text='Beginner:')
        intermidiate_label = Label(record_win, text='Intermidiate:')
        expert_label = Label(record_win, text='Expert:')

        beginner_best = Label(record_win, text='{} seconds'.format(self.record[0][0]))
        intermidiate_best = Label(record_win, text='{} seconds'.format(self.record[1][0]))
        expert_best = Label(record_win, text='{} seconds'.format(self.record[2][0]))

        beginner_name = Label(record_win, text=self.record[0][1])
        intermidiate_name = Label(record_win, text=self.record[1][1])
        expert_name = Label(record_win, text=self.record[2][1])

        beginner_label.grid(row=0, column=0, padx=15, pady=(20, 0), sticky=W)
        intermidiate_label.grid(row=1, column=0, padx=15, sticky=W)
        expert_label.grid(row=2, column=0, padx=15, sticky=W)

        beginner_best.grid(row=0, column=1, pady=(20, 0), sticky=W)
        intermidiate_best.grid(row=1, column=1, sticky=W)
        expert_best.grid(row=2, column=1, sticky=W)

        beginner_name.grid(row=0, column=2, pady=(20, 0), padx=(15, 0), sticky=W)
        intermidiate_name.grid(row=1, column=2, padx=(15, 0), sticky=W)
        expert_name.grid(row=2, column=2, padx=(15, 0), sticky=W)

        record_win.update()

        record_win.mainloop()

    def show_statistics(self):
        stats_window = Toplevel(self.root)
        stats_window.title("Game Statistics")

        if self.user_id:
            stats = fetch_user_statistics(self.connection, self.user_id)
            if stats:
                for i, (game_state, difficulty, score) in enumerate(stats):
                    Label(stats_window, text=f"Game {i + 1}: State: {game_state}, Difficulty: {difficulty}, Score: {score}").pack()
            else:
                Label(stats_window, text="No statistics available").pack()
        else:
            Label(stats_window, text="No user logged in").pack()

    def register(self, username, password, email):
        self.username = username
        register_user(self.connection, username, password, email)
        self.user_id = get_user_id(self.connection, username)

    def save_state(self):
        game_state = "in_progress"  # Replace with actual game state data
        difficulty = 'easy'  # Example difficulty level
        score = 0  # Example score, replace with actual score
        save_game_state(self.connection, self.user_id, game_state, difficulty, score)

    def load_settings(self):
        settings = load_game_settings(self.connection, self.user_id)
        if settings:
            # Load settings into the game
            pass

    def play(self):
        for y in range(self.height):
            self.block.append([])
            for x in range(self.width):
                self.temp_command = partial(self.check_grid, y, x)
                self.right_click_event = partial(self.mark_bomb, y, x)
                self.change_face_event = partial(self.change_face, y, x)
                self.block[y].append(Button(self.root, command=self.temp_command, relief=RAISED, bd=3,
                                            font=Font(weight='bold', family='small fonts', size=7)))
                self.block[y][x].bind('<Button-3>', self.right_click_event)
                self.block[y][x].bind('<ButtonPress-1>', self.change_face_event)
                self.block[y][x].bind('<ButtonRelease-1>', self.change_face_event)
        self.timer_container.place(x=self.width * 20 - 3.5, y=3.5, width=47, height=27, anchor=NE)
        self.bomb_left_counter_container.place(x=3.5, y=3.5, width=47, height=27)
        self.timer_block1.place(x=0, y=0)
        self.timer_block2.place(x=15, y=0)
        self.timer_block3.place(x=30, y=0)
        self.bomb_left_block1.place(x=0, y=0)
        self.bomb_left_block2.place(x=15, y=0)
        self.bomb_left_block3.place(x=30, y=0)
        self.top_container_frame.place(x=10, y=10, width=self.width * 20 + 6, height=40)
        self.top_container.place(x=12, y=12, width=self.width * 20 + 2, height=36)
        self.face_button.place(x=(self.width * 20 + 2) // 2 - 2, y=17, anchor=CENTER, width=25, height=25)
        self.grid_border.place(x=11, y=60, width=self.width * 20 + 4, height=self.height * 20 + 4)
        for y in range(len(self.block)):
            for x in range(len(self.block[y])):
                self.block[y][x].place(x=13 + x * 20, y=62 + y * 20, width=20, height=20)
                self.root.update()

if __name__ == '__main__':
    root = Tk()
    root.title('Minesweeper')
    game = MineSweeper(root, difficulty=0)
    root.mainloop()