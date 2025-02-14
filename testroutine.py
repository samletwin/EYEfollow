from math import pi, sin, cos, floor
from time import time, time_ns, sleep
from enum import Enum, auto
from tkinter import messagebox, simpledialog, Toplevel, Label, Entry, Button, font
from tkinter.messagebox import askyesno, showerror
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
                        # run on thread so we dont stare at screen for 5 sec
                        thread = threading.Thread(target=self.tracker.export_data)
                        thread.daemon = True
                        thread.start()
                        # self.tracker.export_data
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
        self.canvas.itemconfig(self.countdown_text, state='hidden')
        self.time_ref = time()
        self.start_countdown = 1
        self.grade = simpledialog.askinteger("Input", "Enter the level of difficulty (1-10):", minvalue=1, maxvalue=10)
        self.grade_data = config.get_grade_data(self.grade)
        if self.grade_data is None:
            # show error
            showerror("Error", f"Test Data for Grade {self.grade} not found in config file. Please check the config file.")
            self.master.routine_finished(show_popup=False)
            return
        test_config = config.get_text_test_config()

        self.canvas.itemconfig(self.ball, state='hidden')
        self.canvas.itemconfig(self.saccade_ball, state='hidden')

        self.display_text(self.grade_data.message, test_config.minimum_font_size,
                        test_config.padding_hor_px, test_config.padding_ver_px)
        self.canvas.itemconfig(self.countdown_text, state='normal')
        
        self.tracker.start_collection()
        self.master.bind("<KeyPress>", lambda event: self.reading_finished())

        # Start a separate thread for continuous tracking
        self.stop_tracking_event = threading.Event()
        tracking_thread = threading.Thread(target=self.track_user_reading)
        tracking_thread.daemon = True
        tracking_thread.start()

    def reading_finished(self):
        self.master.unbind("<KeyPress>")
        # stop tracker collection
        self.stop_tracking_event.clear()
        self.tracker.stop_collection()
        self.master.show_questions(self.grade_data.questions)

    def transition_to_next_test(self, results):
        # Transition to the next test in the sequence or the main screen
        for result in results:
            self.GTdata[self.current_test]["question"].append(result['question'])
            self.GTdata[self.current_test]["user_answer"].append(result['user_answer'])
            self.GTdata[self.current_test]["correct_answer"].append(result['correct_answer'])
        if len(results) > 0:
            self.GTdata[self.current_test]['grade'] = self.grade
        self.state = Routine_State.update_test
        self.current_test = next(self.test_names, "Done")

    def track_user_reading(self):
        while not self.stop_tracking_event.is_set():
            self.send_tracker_message()
            sleep(0.1) # Adjust the frequency of tracking messages as needed
        
    def wrap_text(self, text: str, max_width, max_height, min_font_size=20):
        font_size = 100  # Starting font size
        words = text.split()
        lines = []
        current_line = ""

        # Create a temporary text object to measure text size
        temp_text_id = self.canvas.create_text(self.master.width/2, self.master.height/2, text="", font=("Arial", font_size, "bold"), justify="center")

        while True:
            # Try wrapping the text with the current font size
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

            # Check if the wrapped text fits within the max height
            self.canvas.itemconfig(temp_text_id, text="\n".join(lines))
            bbox = self.canvas.bbox(temp_text_id)
            text_height = bbox[3] - bbox[1]

            if text_height <= max_height and font_size >= min_font_size:
                break  # The text fits within the constraints
            else:
                # Decrease the font size and try again
                font_size -= 1
                if font_size < min_font_size:
                    break
                lines = []
                current_line = ""
                self.canvas.itemconfig(temp_text_id, font=("Arial", font_size, "bold"))

        # Remove the temporary text object
        y1, y2 = bbox[1], bbox[3]
        self.canvas.delete(temp_text_id)

        return "\n".join(lines), font_size, y1, y2

    def display_text(self, text, min_font_size, padding_hor_px=450, padding_ver_px=300, mode='all'):
        max_width = self.master.width - padding_hor_px  # Set some padding
        max_height = self.master.height - padding_ver_px  # Set some padding
        wrapped_text, font_size, y1, y2 = self.wrap_text(text, max_width, max_height, min_font_size)
        self.generate_gtdata_for_text(wrapped_text, font_size, y1, y2)

        # Update the font of countdown_text to the calculated font size
        self.canvas.itemconfig(self.countdown_text, font=("Arial", font_size, "bold"))

        def type_text(index=0):
            if mode == 'letter':
                if index < len(wrapped_text):
                    self.canvas.itemconfig(self.countdown_text, text=wrapped_text[:index + 1])
                    self.canvas.after(100, type_text, index + 1)
            elif mode == 'word':
                words = wrapped_text.split()
                if index < len(words):
                    self.canvas.itemconfig(self.countdown_text, text=' '.join(words[:index + 1]))
                    self.canvas.after(300, type_text, index + 1)
            elif mode == 'all':
                self.canvas.itemconfig(self.countdown_text, text=wrapped_text)

        type_text()
    
    def generate_gtdata_for_text(self, text: str, font_size, y1, y2):
        # Split the wrapped text into lines
        lines = text.split("\n")
        font_height = font.Font(family='Arial',size=font_size,weight='bold').metrics('linespace')
        self.GTdata[self.current_test] = {"X": [], "Y": [], 
            "Text": [text.replace("\n", "'")], "Font_Size": [font_size], 
            "question": [], "user_answer": [], "correct_answer":[]}

        for i, line in enumerate(lines):
            # Get bounding box for the first and last character of the line
            temp_text_id = self.canvas.create_text(self.master.width/2, self.master.height/2, 
                                                   text=line, font=("Arial", font_size, "bold"))
            bbox = self.canvas.bbox(temp_text_id)
            if bbox:
                x_first = bbox[0]
                x_last = bbox[2]
                self.GTdata[self.current_test]["X"].append(x_first)
                self.GTdata[self.current_test]["X"].append(x_last)
                self.GTdata[self.current_test]["X"].append("NaN") # using NaN to distinguish between lines of text
            # Remove the temporary text object
            self.canvas.delete(temp_text_id)
        # get y data
        y_mid_top = y1 + font_height/2
        y_mid_bottom = y2 - font_height/2
        y_points = [y_mid_top + i * (y_mid_bottom - y_mid_top) / (len(lines)-1) for i in range(1, len(lines))]
        y_points.insert(0, y_mid_top)
        for y in y_points:
            self.GTdata[self.current_test]["Y"].append(y)
            self.GTdata[self.current_test]["Y"].append(y)
            self.GTdata[self.current_test]["Y"].append("NaN")
        print(y_points)
    
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
        padding = self.test_params[self.current_test]["Padding_Px"]
        return lambda t: [(self.master.width / 2, self.master.height - padding),
                          (self.master.width / 2, padding)]

    def horizontal_saccade(self):
        padding = self.test_params[self.current_test]["Padding_Px"]
        return lambda t: [(self.master.width-padding, self.master.height/2), 
                          (padding, self.master.height/2)]

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
        # self.tracker.dfs = {} - this is done in eyetracker.py export_data now
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
