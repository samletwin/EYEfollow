from math import pi, sin, cos, floor
from time import time, time_ns, sleep
from enum import Enum, auto
from tkinter import messagebox, simpledialog, Toplevel, Label, Entry, Button, font
from tkinter.messagebox import askyesno
import traceback
import tkinter as tk
from eyetracker import EyeTracker_DM
import config
import threading

draw_refresh_rate   = 5       # ms
countdown_duration  = 3       # s
state_machine_cycle = 100     # ms

class Routine_State(Enum):
    countdown   = auto()
    update_test = auto()
    drawing     = auto()
    idle        = auto()

class QuestionsDialog(Toplevel):
    def __init__(self, parent, questions, correct_answers):
        super().__init__(parent)
        self.title("Answer the Questions")
        self.answers = []
        self.correct_answers = correct_answers
        
        # Create a list to store Entry widgets or Checkbutton variables
        self.entries = []

        # Create labels and entries for each question
        for i, (question, correct_answer) in enumerate(zip(questions, correct_answers)):
            Label(self, text=f"Q{i+1}: {question}").pack(pady=(10, 0))  # Add some padding for spacing
            if isinstance(correct_answer, bool):
                true_var = tk.BooleanVar()
                false_var = tk.BooleanVar()
                true_checkbox = tk.Checkbutton(self, text="True", variable=true_var, command=lambda fv=false_var: fv.set(False))
                false_checkbox = tk.Checkbutton(self, text="False", variable=false_var, command=lambda tv=true_var: tv.set(False))
                true_checkbox.pack(pady=(0, 5))
                false_checkbox.pack(pady=(0, 10))
                self.entries.append((true_var, false_var))
            else:
                entry = Entry(self, width=50)
                entry.pack(pady=(0, 10))  # Add padding between questions
                self.entries.append(entry)

        # Submit button to collect all answers
        self.submit_button = Button(self, text="Submit", command=self.submit_answers)
        self.submit_button.pack(pady=20)

        # Make sure the window is modal
        self.grab_set()
        self.transient(parent)
        self.parent = parent
        self.result = None

    def submit_answers(self):
        # Collect answers from all entries
        self.answers = []
        for entry in self.entries:
            if isinstance(entry, tuple):  # True/False checkboxes
                true_var, false_var = entry
                if true_var.get():
                    self.answers.append(True)
                elif false_var.get():
                    self.answers.append(False)
                else:
                    self.answers.append(None)  # No selection made
            else:
                self.answers.append(entry.get())
        
        # Display correct answers and indicate if the user's answer was correct
        for i, (entry, correct_answer) in enumerate(zip(self.entries, self.correct_answers)):
            result_text = f"Q{i+1} Correct Answer: {correct_answer}"
            if isinstance(entry, tuple):  # True/False checkboxes
                true_var, false_var = entry
                user_answer = True if true_var.get() else False if false_var.get() else None
                if user_answer == correct_answer:
                    result_text += " ✓"  # Add a checkmark if the answer is correct
            else:
                user_answer = entry.get().strip().lower()
                if user_answer == correct_answer.strip().lower():
                    result_text += " ✓"  # Add a checkmark if the answer is correct
            Label(self, text=result_text, fg="green" if "✓" in result_text else "red").pack(pady=(0, 5))

        # Disable the submit button after submission
        self.submit_button.config(state='disabled')


class Test_Routine:
    def __init__(self, master, canvas: tk.Canvas, ignore_popup):
        self.master = master
        self.canvas = canvas
        self.ignore_popup = ignore_popup
        self.collect_data = True
        if self.collect_data:
            self.tracker = EyeTracker_DM(master=self)
        self.GTdata  = {'ScreenConfig': {'Width':[self.master.width], 'Height':[self.master.height]}}
        self.tracker.set_screen_cfg('ScreenConfig', self.GTdata["ScreenConfig"])

        self.test_params = config.get_full_test_config()
        self.ball_radius = config.get_ball_radius_px()
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
                if self.ignore_popup is not True:
                    if "Text" in self.current_test:
                        messagebox.showinfo("Proceed?", "Read the full text, hit any key upon reading the text to continue. Ready to proceed?")
                    else:
                        messagebox.showinfo("Proceed?", "Are we ready to proceed?")
                self.state = Routine_State.countdown
                if self.current_test != "Done":
                    if "Text" in self.current_test:
                        self.reading_main()
                    else:
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
        grade_data = config.get_grade_data(level)
        test_config = config.get_text_test_config()

        self.canvas.itemconfig(self.countdown_text, state='normal')
        self.canvas.itemconfig(self.ball, state='hidden')
        self.canvas.itemconfig(self.saccade_ball, state='hidden')

        self.GTdata[self.current_test] = {"X": [], "Y": []}  # gt data is filled in display_text
        self.display_text(grade_data.message, test_config.minimum_font_size,
                        test_config.padding_hor_px, test_config.padding_ver_px)
        self.tracker.start_collection()

        # Bind key press event to stop the tracking and ask questions
        self.master.bind("<KeyPress>", lambda event: self.ask_questions(grade_data.questions, grade_data.answers))

        # Start a separate thread for continuous tracking
        self.stop_tracking_event = threading.Event()
        tracking_thread = threading.Thread(target=self.track_user_reading)
        tracking_thread.daemon = True
        tracking_thread.start()

    def track_user_reading(self):
        while not self.stop_tracking_event.is_set():
            self.send_tracker_message()
            sleep(0.1) # Adjust the frequency of tracking messages as needed

    # Modify ask_questions to unbind the keypress event and stop tracking
    def ask_questions(self, questions, correct_answers):
        # Stop tracking and unbind keypress event to prevent multiple triggers
        self.stop_tracking_event.set()
        self.tracker.stop_collection()
        self.master.unbind("<KeyPress>")
        self.canvas.itemconfig(self.countdown_text, state='hidden')
        dialog = QuestionsDialog(self.master, questions, correct_answers)
        self.master.wait_window(dialog)
        self.answers = dialog.answers
        self.show_retry_dialog()
        
    def wrap_text(self, text:str, max_width, font_size):
        words = text.split()
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

    def get_font_size(self, text, max_width, max_height, min_font_size):
        font_size = 35  # Starting font size
        temp_text_id = self.canvas.create_text(0, 0, text=text, font=("Arial", font_size, "bold"))

        # Gradually decrease font size until text fits within the canvas
        while self.canvas.bbox(temp_text_id)[2] > max_width or self.canvas.bbox(temp_text_id)[3] > max_height:
            font_size -= 1
            self.canvas.itemconfig(temp_text_id, font=("Arial", font_size, "bold"))
            if font_size < 20:  # Set a minimum font size limit
                break

        # Remove the temporary text object
        self.canvas.delete(temp_text_id)

        return font_size

    def display_text(self, text, min_font_size, padding_hor_px=20, padding_ver_px=20, mode='all'):
        max_width = self.master.width - padding_hor_px  # Set some padding
        max_height = self.master.height - padding_ver_px  # Set some padding
        font_size = self.get_font_size(text, max_width, max_height, min_font_size)
        wrapped_text = self.wrap_text(text, max_width, font_size)
        self.generate_gtdata_for_text(wrapped_text, font_size)

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
    
    def generate_gtdata_for_text(self, text, font_size):
        # Split the wrapped text into lines
        lines = text.split("\n")
        font_height = font.Font(family='Arial',size=font_size,weight='bold').metrics('linespace')

        for i, line in enumerate(lines):
            # Get bounding box for the first and last character of the line
            temp_text_id = self.canvas.create_text(self.master.width/2, self.master.height/2, 
                                                   text=line, font=("Arial", font_size, "bold"))
            bbox = self.canvas.bbox(temp_text_id)
            if bbox:
                x_first = bbox[0]
                x_last = bbox[2]

                # Store GTData for each line
                self.GTdata[self.current_test]["X"].append(x_first)
                self.GTdata[self.current_test]["X"].append(x_last)
                self.GTdata[self.current_test]["X"].append("NaN") # using NaN to distinguish between lines of text
                
            # Remove the temporary text object
            self.canvas.delete(temp_text_id)
        
        # get y data
        if len(lines) % 2 == 0: #even
            lolz = int(len(lines)/2)
            for i in range(lolz, -lolz, -1):
                # if even, first line y value mid point = (screen height / 2 + [number of lines / 2] * [iter - 0.5] * font height 
                y_midpoint = self.master.height / 2 + (lolz) * (i-0.5) * font_height 
                self.GTdata[self.current_test]["Y"].append(y_midpoint)
                self.GTdata[self.current_test]["Y"].append(y_midpoint)
                self.GTdata[self.current_test]["Y"].append("NaN")
        else: # odd
            # y value mid point = (screen height / 2 + [number of lines / 2] * iter * font height)
            lolz = floor(len(lines)/2)
            for i in range (lolz, -lolz-1, -1):
                y_midpoint = self.master.height / 2 + (lolz) * (i) * font_height 
                self.GTdata[self.current_test]["Y"].append(y_midpoint)
                self.GTdata[self.current_test]["Y"].append(y_midpoint)
                self.GTdata[self.current_test]["Y"].append("NaN")
                

    def show_retry_dialog(self):
        retry = askyesno(title="Retry?", message="Would you like to retry the test?")
        if not retry:
            self.state = Routine_State.update_test
            self.current_test = next(self.test_names, "Done")
        else:
            self.reading_main()
    
    def send_tracker_message(self):
        if self.collect_data:
            try:
                while (msg := self.tracker.read_msg_async()) is not None:
                    self.tracker.tracker_data.append((time(), *msg))
                    self.get_pog(msg)
            except:
                traceback.print_exc()
                pass

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

        self.send_tracker_message()

        if t < self.test_params[self.current_test]["Duration"]:
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
        self.canvas.itemconfig(self.countdown_text, text=f'{self.count}\n{self.test_params[self.current_test]["Instruction"]}',state='normal')
        
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
        return lambda t: (0, 0.95 * cos(2 * pi * self.test_params["Smooth_Vertical"]["Frequency"] * t))

    def smooth_horizontal(self):
        return lambda t: (1.5 * cos(2 * pi * self.test_params["Smooth_Horizontal"]["Frequency"] * t), 0)

    def smooth_circle(self):
        return lambda t: (0.75 * cos(2 * pi * self.test_params["Smooth_Circle"]["Frequency"] * t), 0.75 * sin(2 * pi * self.test_params["Smooth_Circle"]["Frequency"] * t))

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
