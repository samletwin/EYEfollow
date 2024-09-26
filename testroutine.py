from math import pi, sin, cos
from time import time, time_ns
from enum import Enum, auto
from tkinter import messagebox, simpledialog, Toplevel, Label, Entry, Button
from tkinter.messagebox import askyesno
import traceback
import tkinter as tk
from eyetracker import EyeTracker_DM
from config import *


# Constants to control behaviour of the tests
test_params = {
    "Vertical_Saccade": {
        "Duration": 10,     # s
        "Frequency": 1,     # Hz
        "Instruction": "Look back and forth between\ndots as fast as possible"
    },
    "Horizontal_Saccade": {
        "Duration": 10, 
        "Frequency": 1,
        "Instruction": "Look back and forth between\ndots as fast as possible"
    },
    "Smooth_Circle": {
        "Duration": 16, 
        "Frequency": 2/16,
        "Instruction": "Follow the dot"
    },
    "Smooth_Vertical": {
        "Duration": 22.5,
        "Frequency": 3.25/22.5,
        "Instruction": "Follow the dot"
    },
    "Smooth_Horizontal": {
        "Duration": 27,
        "Frequency": 2/27,
        "Instruction": "Follow the dot"
    },
    "Text_Reading": {
        "Duration": 2,
        "Frequency": 1,
        "Instruction": "Read the text on the screen"
    },
}

draw_refresh_rate   = 5       # ms
countdown_duration  = 3       # s
state_machine_cycle = 100     # ms
ball_radius = 12              # px

class Routine_State(Enum):
    countdown   = auto()
    update_test = auto()
    drawing     = auto()
    idle        = auto()

class QuestionsDialog(Toplevel):
    def __init__(self, parent, questions):
        super().__init__(parent)
        self.title("Answer the Questions")
        self.answers = []

        # Create a list to store Entry widgets
        self.entries = []

        # Create labels and entries for each question
        for i, question in enumerate(questions):
            Label(self, text=question).pack(pady=(10, 0))  # Add some padding for spacing
            entry = Entry(self, width=50)
            entry.pack(pady=(0, 10))  # Add padding between questions
            self.entries.append(entry)

        # Submit button to collect all answers
        submit_button = Button(self, text="Submit", command=self.submit_answers)
        submit_button.pack(pady=20)

        # Make sure the window is modal
        self.grab_set()
        self.transient(parent)
        self.parent = parent
        self.result = None

    def submit_answers(self):
        # Collect answers from all entries
        self.answers = [entry.get() for entry in self.entries]
        self.destroy()  # Close the dialog

class Test_Routine:
    def __init__(self, master, canvas: tk.Canvas):
        self.master = master
        self.canvas = canvas

        self.collect_data = True
        if self.collect_data:
            self.tracker = EyeTracker_DM(master=self)
        self.GTdata={}

        self.ball_radius = ball_radius
        self.ball = self.canvas.create_oval(0, 0, self.ball_radius, self.ball_radius, fill="white")
        self.canvas.itemconfig(self.ball, state='hidden')

        self.saccade_ball = self.canvas.create_oval(0, 0, self.ball_radius, self.ball_radius, fill="white")
        self.canvas.itemconfig(self.saccade_ball, state='hidden')

        self.participant_name = "Default Participant"

        self.count = countdown_duration
        self.countdown_text = self.canvas.create_text(self.master.width/2, self.master.height/2, text=self.count,
                                                      font=("Arial", 35, "bold"), justify='center', fill="white")
        self.canvas.itemconfig(self.countdown_text, state='hidden')

        self.variable_reset()

        self.main_function()

    def main_function(self):
        if self.state == Routine_State.update_test:
            if self.current_test == "Done":
                self.master.routine_finished()
                if self.collect_data:
                    try:
                        self.tracker.export_data()
                    except:
                        traceback.print_exc()
                self.cancel()
            else:
                self.time_ref = time()
                self.start_countdown = 1
                messagebox.showinfo("Proceed?", "Are we ready to proceed?")
                self.state = Routine_State.countdown
                if self.current_test != "Done":
                    if "Text" in self.current_test:
                        self.reading_main()

                    self.GTdata[self.current_test]={}
                    for key in ["Time", "X", "Y"]:
                        self.GTdata[self.current_test][key]=[]
                    if "Saccade" in self.current_test:
                        if self.current_test == "Vertical_Saccade":
                            f = self.vertical_saccade()
                        else:
                            f = self.horizontal_saccade()

                        sac_coords = f(0)
                        self.GTdata[self.current_test].pop("Time")
                        self.GTdata[self.current_test]["X"].append(sac_coords[0][0])
                        self.GTdata[self.current_test]["X"].append(sac_coords[1][0])
                        self.GTdata[self.current_test]["Y"].append(sac_coords[0][1])
                        self.GTdata[self.current_test]["Y"].append(sac_coords[1][1])
                        print(self.GTdata[self.current_test])

        elif self.state == Routine_State.countdown:
            if "Text" not in self.current_test:
                if self.start_countdown:
                    self.update_countdown()
                else:
                    self.start_drawing = 1
                    self.state = Routine_State.drawing
                    if self.collect_data:
                        self.tracker.start_collection()
                    
        elif self.state == Routine_State.drawing:
            if "Text" not in self.current_test:
                if self.start_drawing:
                    self.start_drawing = 0
                    self.time_ref = time()
                    self.canvas.itemconfig(self.ball, state="normal")
                    self.draw()
                elif not self.start_drawing and self.drawing_finished:
                    self.drawing_finished = 0
                    self.state = Routine_State.update_test
                    if self.collect_data:
                        self.tracker.stop_collection()
                    if not askyesno(title="Retry?", message="Would you like to retry the test?"):
                        self.current_test = next(self.test_names, "Done")

        elif self.state == Routine_State.idle:
            pass

        self.move_ball_ref = self.canvas.after(state_machine_cycle, self.main_function)

    def reading_main(self):
        self.time_ref = time()
        self.start_countdown = 1
        level = simpledialog.askinteger("Input", "Enter the level of difficulty (1-10):", minvalue=1, maxvalue=10)
        grade_data = get_grade_data(level)
        
        self.canvas.itemconfig(self.countdown_text, state='normal')
        self.canvas.itemconfig(self.ball, state='hidden')
        self.canvas.itemconfig(self.saccade_ball, state='hidden')
        self.display_text(grade_data.message)
        self.canvas.after(5000, self.ask_questions, grade_data.questions)
        
    def wrap_text(self, text:str, max_width, font_size):
        words = text.split()
        print(words)
        lines = []
        current_line = ""

        # Create a temporary text object to measure text size
        temp_text_id = self.canvas.create_text(0, 0, text="", font=("Arial", font_size, "bold"))

        for word in words:
            # Measure the current line with the new word
            self.canvas.itemconfig(temp_text_id, text=(current_line + " " + word).strip())
            bbox = self.canvas.bbox(temp_text_id)
            width = bbox[2] - bbox[0]
            if width > max_width:
                # If the current line width exceeds max width, start a new line
                lines.append(current_line.strip())
                current_line = word
            else:
                # Add the word to the current line
                current_line += " " + word if current_line else word

        # Add the last line
        lines.append(current_line.strip())

        # Remove the temporary text object
        self.canvas.delete(temp_text_id)

        return "\n".join(lines)

    def get_font_size(self, text, max_width, max_height):
        font_size = 35  # Starting font size
        temp_text_id = self.canvas.create_text(0, 0, text=text, font=("Arial", font_size, "bold"))

        # Gradually decrease font size until text fits within the canvas
        while self.canvas.bbox(temp_text_id)[2] > max_width or self.canvas.bbox(temp_text_id)[3] > max_height:
            font_size -= 1
            self.canvas.itemconfig(temp_text_id, font=("Arial", font_size, "bold"))
            if font_size < 10:  # Set a minimum font size limit
                break

        # Remove the temporary text object
        self.canvas.delete(temp_text_id)

        return font_size

    def display_text(self, text, mode='all'):
        max_width = self.master.width - 20  # Set some padding
        max_height = self.master.height - 20  # Set some padding
        font_size = self.get_font_size(text, max_width, max_height)
        wrapped_text = self.wrap_text(text, max_width, font_size)

        retry_time = 5000
        # Update the font of countdown_text to the calculated font size
        self.canvas.itemconfig(self.countdown_text, font=("Arial", font_size, "bold"))

        def type_text(index=0):
            if mode == 'letter':
                if index < len(wrapped_text):
                    self.canvas.itemconfig(self.countdown_text, text=wrapped_text[:index+1])
                    self.canvas.after(100, type_text, index+1)
            elif mode == 'word':
                words = wrapped_text.split()
                if index < len(words):
                    self.canvas.itemconfig(self.countdown_text, text=' '.join(words[:index+1]))
                    self.canvas.after(300, type_text, index+1)
            elif mode == 'all':
                self.canvas.itemconfig(self.countdown_text, text=wrapped_text)

        type_text()

    def show_retry_dialog(self):
        retry = askyesno(title="Retry?", message="Would you like to retry the test?")
        if not retry:
            self.state = Routine_State.update_test
            self.current_test = next(self.test_names, "Done")
        else:
            self.reading_main()

    def ask_questions(self, questions):
        dialog = QuestionsDialog(self.master, questions)
        self.master.wait_window(dialog)
        self.answers = dialog.answers
        self.show_retry_dialog()


    def draw(self):
        t = time_ns()/1e9 - self.time_ref

        if "Saccade" in self.current_test:
            top_ball_colour, bottom_ball_colour = self.saccade_colour_monitor()

            self.canvas.itemconfig(self.ball, fill=top_ball_colour)
            self.canvas.itemconfig(self.saccade_ball, fill=bottom_ball_colour)
        else:
            x_cen, y_cen = self.get_coords(self.current_test, t)
            self.canvas.moveto(self.ball, x_cen - self.ball_radius/2, y_cen - self.ball_radius/2)
            self.canvas.configure(bg="black")

        if self.collect_data:
            try:
                while (msg := self.tracker.read_msg_async()) is not None:
                    self.tracker.tracker_data.append((time(), *msg))
                    self.get_pog(msg)
            except:
                traceback.print_exc()
                pass

        if t < test_params[self.current_test]["Duration"]:
            self.draw_ref = self.canvas.after(draw_refresh_rate, self.draw)
        else:
            self.canvas.itemconfig(self.ball, state="hidden", fill='white')
            self.canvas.itemconfig(self.saccade_ball, state="hidden", fill='white')
            self.drawing_finished = 1

    def update_countdown(self):
        radius = 50 - ((50 - self.ball_radius)/countdown_duration)*(countdown_duration-self.count)

        if "Saccade" in self.current_test:
            ball_coords, saccade_ball_coords = self.get_coords(self.current_test, 0)
            self.canvas.moveto(self.ball, ball_coords[0] - self.ball_radius/2, ball_coords[1] - self.ball_radius/2)
            self.canvas.moveto(self.saccade_ball, saccade_ball_coords[0] - self.ball_radius/2, saccade_ball_coords[1] - self.ball_radius/2)
            self.canvas.itemconfig(self.saccade_ball, state="normal")
        else:
            x_cen, y_cen = self.get_coords(self.current_test, 0)
            self.canvas.coords(self.ball, x_cen-radius/2, y_cen-radius/2, x_cen+radius/2, y_cen+radius/2)
        
        self.canvas.itemconfig(self.ball, state="normal")
        self.canvas.itemconfig(self.countdown_text, text=f'{self.count}\n{test_params[self.current_test]["Instruction"]}',state='normal')
        
        if time() - self.time_ref >= 1:  
            self.count -= 1
            self.time_ref = time()

        if self.count <= -1:
            self.start_countdown = 0
            self.canvas.itemconfig(self.countdown_text,state='hidden')
            self.count = countdown_duration
        
    def get_coords(self, test, t):
        if test == "Vertical_Saccade":
            f = self.vertical_saccade()
        elif test == "Horizontal_Saccade":
            f = self.horizontal_saccade()
        elif test == "Smooth_Vertical":
            f = self.smooth_vertical()
        elif test == "Smooth_Horizontal":
            f = self.smooth_horizontal()
        elif test == "Smooth_Circle":
            f = self.smooth_circle()
        elif test == "Text_Reading":
            f = self.text_reading()
        
        if "Saccade" in self.current_test:
            return f(t)
        else:
            x_cen = self.master.width / 2 + self.master.height*(f(t)[0]/2)
            y_cen = self.master.height*(1/2 + f(t)[1]/2)
            self.GTdata[test]["Time"].append(t)
            self.GTdata[test]["X"].append(x_cen)
            self.GTdata[test]["Y"].append(y_cen)
            return x_cen, y_cen 

    def vertical_saccade(self):
        return lambda t: [(self.master.width / 2, self.master.height*(1/2+0.75/2)),
                          (self.master.width / 2, self.master.height*(1/2-0.75/2))]

    def horizontal_saccade(self):
        return lambda t: [(self.master.width / 2 + self.master.height*1.5/2, self.master.height/2), 
                          (self.master.width / 2 - self.master.height*1.5/2, self.master.height/2)]

    def smooth_vertical(self):
        return lambda t: (0, 0.95 * cos(2 * pi * test_params["Smooth_Vertical"]["Frequency"] * t))

    def smooth_horizontal(self):
        return lambda t: (1.5 * cos(2 * pi * test_params["Smooth_Horizontal"]["Frequency"] * t), 0)

    def smooth_circle(self):
        return lambda t: (0.75 * cos(2 * pi * test_params["Smooth_Circle"]["Frequency"] * t), 0.75 * sin(2 * pi * test_params["Smooth_Circle"]["Frequency"] * t))

    def get_pog(self, msg):
        if "TIME" in msg[1].keys():
            self.left_eye_pog = [float(msg[1]["LPOGX"]), float(msg[1]["LPOGY"])]
            self.right_eye_pog = [float(msg[1]["RPOGX"]), float(msg[1]["RPOGY"])]
        else:
            self.left_eye_pog = [0, 0]
            self.right_eye_pog = [0, 0]

    def saccade_colour_monitor(self):
        if self.current_test == "Vertical_Saccade":
            if self.right_eye_pog[1] > 0.55 and self.left_eye_pog[1] > 0.55:
                top_ball_colour = "green"
                bottom_ball_colour = "white"
            elif self.right_eye_pog[1] < 0.55 and self.left_eye_pog[1] < 0.55:
                top_ball_colour = "white"
                bottom_ball_colour = "green"
            else:
                top_ball_colour = "white"
                bottom_ball_colour = "white"
        elif self.current_test == "Horizontal_Saccade":
            if self.right_eye_pog[0] > 0.55 and self.left_eye_pog[0] > 0.55:
                top_ball_colour = "green"
                bottom_ball_colour = "white"
            elif self.right_eye_pog[0] < 0.55 and self.left_eye_pog[0] < 0.55:
                top_ball_colour = "white"
                bottom_ball_colour = "green"
            else:
                top_ball_colour = "white"
                bottom_ball_colour = "white"

        return top_ball_colour, bottom_ball_colour

    def variable_reset(self):
        self.tracker.dfs = {}
        self.left_eye_pog = [0, 0]
        self.right_eye_pog = [0, 0]

        self.state = Routine_State.idle
        self.test_names = []
        self.current_test = None
        self.tracker.current_test = None
        self.start_countdown = 0
        self.start_drawing = 0
        self.drawing_finished = 0
    
    def cancel(self):
        try:
            self.draw_ref = self.canvas.after_cancel(self.draw_ref)
        except:
            pass

        if self.collect_data and self.state is not Routine_State.countdown:    
            self.tracker.stop_collection()
        
        self.canvas.itemconfig(self.countdown_text, state='hidden')
        self.canvas.itemconfig(self.ball, state="hidden")
        self.canvas.coords(self.ball, 0, 0, self.ball_radius, self.ball_radius)
        self.canvas.itemconfig(self.saccade_ball, state="hidden")

        self.variable_reset()
