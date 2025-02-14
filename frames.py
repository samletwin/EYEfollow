'''
EYEfollow 1.1
Home Screen Class
Gian Favero, Steven Caro and Joshua Picchioni
2024
'''

import tkinter as tk
from math import pi, sin, cos
from time import time
from PIL import Image, ImageTk, ImageGrab
from tkinter import ttk
from tkinter.messagebox import *
import os
from processing import process_excel_file
from images_to_pdf import images_to_pdf
import threading
from dataclasses import dataclass
import pandas as pd
from tkinter import font
import traceback
from typing import Dict, List
from config import config_handler, TestParams


class PreviewCanvas(tk.Canvas):
    def __init__(self, master, test_name):
        super().__init__(master, width=300, height=200, bg="black")
        self.test_name = test_name
        self.ball_radius = config_handler.get_ball_radius()
        self.ball = self.create_oval(0, 0, self.ball_radius, self.ball_radius, fill="white")
        self.animate = False

    def update_preview(self, params):
        self.params = params
        self.draw()

    def draw(self):
        self.delete("all")
        if self.animate:
            self.after_cancel(self.animate)
        
        # Simplified drawing logic from Test_Routine
        if "Saccade" in self.test_name:
            pos1 = (100, 50)
            pos2 = (200, 150)
            self.create_oval(pos1[0]-5, pos1[1]-5, pos1[0]+5, pos1[1]+5, fill="white")
            self.create_oval(pos2[0]-5, pos2[1]-5, pos2[0]+5, pos2[1]+5, fill="white")
        else:
            x = 150 + 100 * cos(2 * pi * self.params.get('Frequency', 1) * time())
            y = 100 + 50 * sin(2 * pi * self.params.get('Frequency', 1) * time())
            self.create_oval(x-5, y-5, x+5, y+5, fill="white")
        
        self.animate = self.after(50, self.draw)

class SettingsWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Test Configuration Settings")
        self.geometry("1000x700")
        self.config_handler = config_handler
        
        self.notebook = ttk.Notebook(self)
        self.create_general_tab()
        self.create_test_tabs()
        self.entries_for_test_name:Dict[str, List[str]] = {}
        self.notebook.pack(expand=True, fill='both')
        
        ttk.Button(self, text="Save", command=self.save_settings).pack(pady=10)

    def create_general_tab(self):
        tab = ttk.Frame(self.notebook)
        ttk.Label(tab, text="Ball Radius (px):").grid(row=0, column=0)
        self.ball_radius_entry = ttk.Entry(tab)
        self.ball_radius_entry.insert(0, str(self.config_handler.get_ball_radius()))
        self.ball_radius_entry.grid(row=0, column=1)
        self.notebook.add(tab, text="General")

    def create_test_tabs(self):
        for test_name, params in self.config_handler.get_all_test_params().items():
            tab = ttk.Frame(self.notebook)
            self.create_test_controls(tab, test_name, params)
            self.notebook.add(tab, text=test_name.replace("_", " "))

    def create_test_controls(self, tab, test_name: str, params: TestParams):
        # Preview Canvas
        preview_frame = ttk.Frame(tab)
        preview_frame.grid(row=0, column=2, rowspan=4, padx=10)
        self.preview = PreviewCanvas(preview_frame, test_name)
        self.preview.pack(pady=10)
        self.preview.draw()

        row = 0
        # Parameter controls
        if test_name == "Text_Reading":
            ttk.Label(tab, text="Minimum:").grid(row=row, column=0)
            font_entry = ttk.Entry(tab)
            font_entry.insert(0, str(params.minimum_font_size)
            font_entry.grid(row=row, column=1)
            row += 1

            ttk.Label(tab, text="Horizontal Padding (Px):").grid(row=row, column=0)
            horizontal_entry = ttk.Entry(tab)
            horizontal_entry.insert(0, str(params.padding_horizontal_px)
            horizontal_entry.grid(row=row, column=1)
            row += 1

            ttk.Label(tab, text="Vertical Padding (Px):").grid(row=row, column=0)
            vertical_entry = ttk.Entry(tab)
            vertical_entry.insert(0, str(params.padding_vertical_px)
            vertical_entry.grid(row=row, column=1)
            row += 1
        else:
            ttk.Label(tab, text="Duration:").grid(row=row, column=0)
            duration_entry = ttk.Entry(tab)
            duration_entry.insert(0, str(params.duration)
            duration_entry.grid(row=row, column=1)
            row += 1

            ttk.Label(tab, text="Frequency:").grid(row=row, column=0)
            freq_entry = ttk.Entry(tab)
            freq_entry.insert(0, str(params.get('Frequency', '')))
            freq_entry.grid(row=row, column=1)
            row += 1

        # Add input validation and preview updates
        for entry in [duration_entry, freq_entry]:
            entry.bind("<KeyRelease>", lambda e: self.update_preview(test_name))

    def update_preview(self, test_name):
        params = {
            'Duration': float(self.get_entry_value(test_name, 'Duration')),
            'Frequency': float(self.get_entry_value(test_name, 'Frequency'))
        }
        self.preview.update_preview(params)

    def save_settings(self):
        # Save general settings
        self.config_handler.update_test_param('general', 'ball_radius_px', 
                                            int(self.ball_radius_entry.get()))
        
        # Save test-specific settings
        for test_name in self.config_handler.get_all_test_names():
            params = {
                'Duration': float(self.get_entry_value(test_name, 'Duration')),
                'Frequency': float(self.get_entry_value(test_name, 'Frequency'))
            }
            for param, value in params.items():
                self.config_handler.update_test_param(test_name, param, value)
        
        self.config_handler.save_config()
        showinfo("Saved", "Settings updated successfully")
        self.destroy()

class Home_Screen(tk.Frame):
    '''
    Class to represent the "Home Screen" of the application
    '''
    def __init__(self, master, controller):
        tk.Frame.__init__(self, master)
        
        self.controller = controller

        # Configure the screen/frame grid
        self.configure_grid()

        # Create the test option buttons
        self.VS_b = tk.Button(self, text = 'Vertical Saccade', bg = "white",
                              command=lambda: [self.onOff("Vertical_Saccade")])
        self.HS_b = tk.Button(self, text = 'Horizontal Saccade', bg = "white",
                              command=lambda: [self.onOff("Horizontal_Saccade")])
        self.SC_b = tk.Button(self, text = 'Smooth Circle', bg = "white", 
                              command=lambda: [self.onOff("Smooth_Circle")])
        self.SV_b = tk.Button(self, text = 'Smooth Vertical', bg="white",
                              command=lambda: [self.onOff("Smooth_Vertical")])
        self.SH_b = tk.Button(self, text = 'Smooth Horizontal', bg="white",
                              command=lambda: [self.onOff("Smooth_Horizontal")])
        self.TR_b = tk.Button(self, text = 'Text Reading', bg="white",
                              command=lambda: [self.onOff("Text_Reading")])
        self.start_b = tk.Button(self, text = 'START', bg = "#eee", state="disabled", height=5, width=20, 
                              command=lambda:self.controller.create_test_routine())
        self.results_b = tk.Button(self, text = 'Results', bg = "white", height=5, width=20, 
                              command=lambda:self.controller.show_results())
        
        self.settings_b = tk.Button(self, text="⚙ Settings", bg="white", command=self.open_settings)
        self.settings_b.grid(row=4, column=0, columnspan=9, pady=10)
        # Place logo png
        logo_image = Image.open("images/Logo.png")
        logo_photo_image = ImageTk.PhotoImage(logo_image)
        logo_label = tk.Label(self, image=logo_photo_image, bg="white")
        logo_label.image = logo_photo_image

        logo_label.grid(row=0, columnspan=20, pady=100)

        # Layout the test option buttons nicely in the frame
        self.VS_b.grid(row=1, column=2, padx=10)
        self.HS_b.grid(row=1, column=3, padx=10)
        self.SC_b.grid(row=1, column=4, padx=10)
        self.SV_b.grid(row=1, column=5, padx=10)
        self.SH_b.grid(row=1, column=6, padx=10)
        self.TR_b.grid(row=1, column=7, padx=10)
        self.start_b.grid(row=2, column=0, columnspan = 9, pady=50)
        self.results_b.grid(row=3, column=0, columnspan = 9, pady=50)

    def open_settings(self):
        SettingsWindow(self.master)

    def configure_grid(self):
        '''
        Configure the grid and background colour of the Home Screen
        '''
        self.configure(bg="white")
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(8, weight=1)
        
    def onOff(self, button_name, reset=0):
        '''
        Event handler for the press of a test option button
        Desired behaviour: Change button colour, "activate" button in controlling class
        '''
        self.controller.activate_button(button_name)            

        if self.controller.activeButtons[button_name] is True:
            if button_name =="Vertical_Saccade":
                self.VS_b.configure(bg="#adffab")
            elif button_name == "Horizontal_Saccade":
                self.HS_b.configure(bg="#adffab")
            elif button_name == "Smooth_Circle":
                self.SC_b.configure(bg="#adffab")
            elif button_name == "Smooth_Vertical":
                self.SV_b.configure(bg="#adffab")
            elif button_name == "Smooth_Horizontal":
                self.SH_b.configure(bg="#adffab")
            elif button_name == "Text_Reading":
                self.TR_b.configure(bg="#adffab")
        else:
            if button_name == "Vertical_Saccade":
                self.VS_b.configure(bg="white")
            elif button_name == "Horizontal_Saccade":
                self.HS_b.configure(bg="white")
            elif button_name == "Smooth_Circle":
                self.SC_b.configure(bg="white")
            elif button_name == "Smooth_Vertical":
                self.SV_b.configure(bg="white")
            elif button_name == "Smooth_Horizontal":
                self.SH_b.configure(bg="white")
            elif button_name == "Text_Reading":
                self.TR_b.configure(bg="white")

        self.start_b.configure(state="disabled", bg="#eee")

        for item in self.controller.activeButtons:
            if self.controller.activeButtons[item] is True:
                self.start_b.configure(state="normal", bg="#adffab")
                break

    def reset_buttons(self):
        self.VS_b.configure(bg="white")
        self.HS_b.configure(bg="white")
        self.SC_b.configure(bg="white")
        self.SV_b.configure(bg="white")
        self.SH_b.configure(bg="white")
        self.TR_b.configure(bg="white")
        self.start_b.configure(state="disabled", bg="#eee")

class QuestionsFrame(tk.Frame):
    """
    Frame to display questions and collect answers.
    """
    def __init__(self, master, controller, questions):
        super().__init__(master)
        self.controller = controller
        self.questions = questions
        self.user_answers = []
        self.configure(bg="black", cursor="arrow")
        self.frame = tk.Frame(self, bg="black")
        self.frame.pack(expand=True, fill="both")  # Main frame expands to fill available space
        self.selected_button_index = {}
        self.current_question_index = 0
        self.create_question_widgets()

    def create_question_widgets(self):
        # Create a content frame centered in the main frame
        self.content_frame = tk.Frame(self.frame, bg="black")
        self.content_frame.place(relx=0.5, rely=0.5, anchor="center")  # Center the content frame

        # Store state for answers
        self.selected_answers = {}  # To track selected answers for each question
        self.correct_answers = {}  # To store correct answers
        self.option_widgets = {}  # To store option widgets for highlighting

        self.question_label = tk.Label(self.content_frame, text="", bg="black", fg="white", font=("Arial", 16))
        self.question_label.pack(anchor="center", pady=20)

        self.option_buttons = []
        for i in range(4):
            button = tk.Radiobutton(self.content_frame, text="", bg="black", fg="white", font=("Arial", 14), 
                                    variable=tk.IntVar(), value=i, 
                                    command=lambda q=i: self.store_answer(q))
            button.pack(anchor="center", padx=20, pady=5)
            self.option_buttons.append(button)

        self.navigation_frame = tk.Frame(self.content_frame, bg="black")
        self.navigation_frame.pack(pady=20)

        self.back_button = tk.Button(self.navigation_frame, text="Back", command=self.show_previous_question, state="disabled")
        self.back_button.pack(side="left", padx=10)

        self.next_button = tk.Button(self.navigation_frame, text="Next", command=self.show_next_question)
        self.next_button.pack(side="right", padx=10)

        self.submit_button = tk.Button(self.navigation_frame, text="Submit", command=self.submit_answers, state="disabled")
        self.submit_button.pack(side="right", padx=10)

        self.show_question()

    # The rest of the methods remain unchanged as in the original code
    def show_question(self, going_back=False):
        selected_question_text = None
        if going_back is True:
            selected_question_text = self.selected_answers.get(self.current_question_index)
            self.selected_question = True
        else:
            self.selected_question = False
        question = self.questions[self.current_question_index]
        self.question_label.config(text=question["message"])

        for i, option in enumerate(question["options"]):
            self.option_buttons[i].config(text=option, value=i, bg="black")
            if option == selected_question_text:
                self.option_buttons[i].config(bg="red")

        self.update_navigation_buttons()

    def store_answer(self, btn_index):
        # highlight selected answer as well
        self.selected_question = True
        for i, radio_button in enumerate(self.option_buttons):
            if i == btn_index:
                radio_button.configure(bg="red")
                selected_option = radio_button["text"]
            else:
                radio_button.configure(bg="black")
        self.selected_answers[self.current_question_index] = selected_option
        self.update_navigation_buttons()

    def show_next_question(self):
        self.current_question_index += 1
        self.show_question()

    def show_previous_question(self):
        self.current_question_index -= 1
        self.show_question(True)

    def update_navigation_buttons(self):
        if self.current_question_index == 0:
            self.back_button.config(state="disabled")
        else:
            self.back_button.config(state="normal")

        if self.current_question_index == len(self.questions) - 1:
            self.next_button.config(state="disabled")
            if self.selected_question is True:
                self.submit_button.config(state="normal")
        else:
            if self.selected_question is True:
                self.next_button.config(state="normal")
            else:
                self.next_button.config(state="disabled")
            self.submit_button.config(state="disabled")

    def submit_answers(self):
        results = []
        score = sum(1 for i, question in enumerate(self.questions) if self.selected_answers.get(i) == question["answer"])
        for i, question in enumerate(self.questions):
            results.append({
                "question": question["message"],
                "user_answer": self.selected_answers[i],
                "correct_answer": question["answer"]
            })
        self.handle_results(score, results)

    def handle_results(self, score, results):
        self.question_label.config(text=f"Your score: {score}/{len(self.questions)}\nPress any key to continue")
        self.controller.bind("<KeyPress>", lambda event: self.controller.handle_question_results(results))
        for button in self.option_buttons:
            button.pack_forget()
        self.back_button.pack_forget()
        self.next_button.pack_forget()
        self.submit_button.pack_forget()


class Results_Frame(tk.Frame):
    def __init__(self, master, controller, input_directory):
        super().__init__(master)
        self.controller = controller
        self.input_directory = input_directory
        self.configure(bg="white")

        self.enabled_buttons = {}
        self.image_paths = []
        self.file_name = ''
        self.text_reading_gaze_data = {}
        self.user_answers = []
        self.grade = 0

        self.draw_top_row()

        # Buttons for different result types (initially disabled)
        self.buttons_grid = ttk.Frame(self)
        self.VS_button = tk.Button(self.buttons_grid, text='Vertical Saccade', command=self.show_vertical_saccade, state='disabled')
        self.HS_button = tk.Button(self.buttons_grid, text='Horizontal Saccade', command=self.show_horizontal_saccade, state='disabled')
        self.SC_button = tk.Button(self.buttons_grid, text='Smooth Circle', command=self.show_smooth_circle, state='disabled')
        self.SV_button = tk.Button(self.buttons_grid, text='Smooth Vertical', command=self.show_smooth_vertical, state='disabled')
        self.SH_button = tk.Button(self.buttons_grid, text='Smooth Horizontal', command=self.show_smooth_horizontal, state='disabled')
        self.TR_button = tk.Button(self.buttons_grid, text='Text Reading', command=self.show_text_reading, state='disabled')

        self.VS_button.grid(row=0, column=0, padx=10, pady=5, sticky='ew') # fill vertically
        self.HS_button.grid(row=1, column=0, padx=10, pady=5, sticky='ew')
        self.SC_button.grid(row=2, column=0, padx=10, pady=5, sticky='ew')
        self.SV_button.grid(row=3, column=0, padx=10, pady=5, sticky='ew')
        self.SH_button.grid(row=4, column=0, padx=10, pady=5, sticky='ew')
        self.TR_button.grid(row=5, column=0, padx=10, pady=5, sticky='ew')

        self.buttons_grid.grid(row=1,column=0,padx=10, pady=10)

        # Canvas to display results
        self.result_canvas = TextReadingResultsCanvas(self, self.input_directory, self.master.winfo_rootx(), self.master.winfo_rooty(), bg="gray")
        self.result_canvas.grid(row=1, column=1, rowspan=6, padx=10, pady=5, sticky="nsew")

        # Exit button to go back to home screen
        self.exit_button = tk.Button(self, text="Exit", command=self.exit_results)
        self.exit_button.grid(row=7, column=0, columnspan=10, padx=20, pady=10, sticky="ew")

        # Configure row and column weights
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.animate_text = False
        self.animate_counter = 0

    def draw_top_row(self):
        self.top_row_grid = ttk.Frame(self)
        # Dropdown to select Excel file
        self.file_label = tk.Label(self.top_row_grid, text="Select Excel File:", bg="white")
        self.file_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.file_dropdown = ttk.Combobox(self.top_row_grid, state="readonly")
        self.file_dropdown['values'] = self.get_excel_files()
        self.file_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Confirm button to select file
        self.confirm_button = tk.Button(self.top_row_grid, text="Confirm", command=self.confirm_file_selection)
        self.confirm_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        # button to export results to pdf
        self.to_pdf_button = tk.Button(self.top_row_grid, text="Export to PDF", 
            command=lambda: self.export_to_pdf(), state='disabled')
        self.to_pdf_button.grid(row=0, column=3, padx=10, pady=10, sticky="e")
        self.top_row_grid.grid(row=0, column=0, columnspan=10, padx=10, pady=10, sticky="ew")

    def export_to_pdf(self):
        if self.text_reading_shown_flag is False and self.text_reading_parsed_flag is True:
            # need to show the text on the canvas so it can be saved as an image - this is not great but oh well
            self.show_text_reading()
        images_to_pdf(self.image_paths, f"{self.input_directory}/{self.file_name}.pdf", self.file_name, self.user_answers, self.grade)

    def tkraise(self, aboveThis=None):
        super().tkraise(aboveThis)
        # update excel files
        self.file_dropdown['values'] = self.get_excel_files()

    def get_excel_files(self):
        """Retrieve a list of Excel files from the input directory."""
        return [f for f in os.listdir(self.input_directory) if f.endswith('.xlsx') and not f.endswith('_GT.xlsx')]

    def confirm_file_selection(self):
        """Process the selected Excel file and enable buttons based on data availability."""
        self.text_reading_shown_flag = False
        selected_file = self.file_dropdown.get()
        if not selected_file:
            return

        file_path = os.path.join(self.input_directory, selected_file)
        self.file_name, file_extension = os.path.splitext(selected_file)
        file_name_gt = self.file_name + '_GT' + file_extension
        file_path_gt = os.path.join(self.input_directory, file_name_gt)
        self.start_processing(file_path, file_path_gt)

    def animate_text_func(self):
        self.result_canvas.configure(bg="gray")
        dots = '.'*self.animate_counter
        self.animate_counter += 1 
        if self.animate_counter > 3:
            self.animate_counter = 1
        if self.animate_text is True:
            self.result_canvas.delete('all')
            self.result_canvas.create_text(self.result_canvas.winfo_width() // 2, self.result_canvas.winfo_height() // 2, text=f"Processing file{dots}", font=("Helvetica", 16))
            self.result_canvas.after(500, self.animate_text_func)

    def start_processing(self, file_path, file_path_gt):
        def thread_function():
            nonlocal file_path, file_path_gt
            # Process the file in the background
            self.enabled_buttons, self.text_reading_gaze_data = process_excel_file(file_path, file_path_gt, self.input_directory)
            self.text_reading_parsed_flag = self.result_canvas.parse_excel(file_path_gt)
            self.user_answers = self.result_canvas.user_answers
            self.grade = self.result_canvas.grade
            if self.text_reading_parsed_flag is False:
                self.enabled_buttons['Text_Reading'] = False
            self.image_paths = [f"{self.input_directory}/{sheet}.png" for sheet in self.enabled_buttons.keys() if self.enabled_buttons[sheet] == True]
            
            # Now that processing is done, use `after` to safely update the canvas in the main thread
            self.result_canvas.after(0, self.update_canvas_with_file_results)

        # Display "Processing file..." immediately
        self.animate_text = True
        self.animate_counter = 0
        self.animate_text_func()

        # Start the thread
        thread = threading.Thread(target=thread_function)
        thread.start()

    def update_canvas_with_file_results(self):
        # delete prev text
        self.animate_text = False
        self.animate_counter = 0
        self.result_canvas.delete("all")
        
        self.result_canvas.configure(bg="gray")
        self.result_canvas.create_text(self.result_canvas.winfo_width() // 2, self.result_canvas.winfo_height() // 2, text=f"Processing complete!~", font=("Helvetica", 16))

        # Enable buttons based on the result of file processing
        if any(self.enabled_buttons.values()):
            self.to_pdf_button.config(state='normal')
        self.VS_button.config(state='normal' if self.enabled_buttons.get('Vertical_Saccade') else 'disabled')
        self.HS_button.config(state='normal' if self.enabled_buttons.get('Horizontal_Saccade') else 'disabled')
        self.SC_button.config(state='normal' if self.enabled_buttons.get('Smooth_Circle') else 'disabled')
        self.SV_button.config(state='normal' if self.enabled_buttons.get('Smooth_Vertical') else 'disabled')
        self.SH_button.config(state='normal' if self.enabled_buttons.get('Smooth_Horizontal') else 'disabled')
        self.TR_button.config(state='normal' if self.enabled_buttons.get('Text_Reading') else 'disabled')

        # Display message if no data is available
        if not any(self.enabled_buttons.values()):
            self.result_canvas.delete("all")
            self.result_canvas.create_text(self.result_canvas.winfo_width() // 2, self.result_canvas.winfo_height() // 2, text="No data present", fill="black", font=("Helvetica", 16))

    def show_vertical_saccade(self):
        self.display_image(f'{self.input_directory}/Vertical_Saccade.png')

    def show_horizontal_saccade(self):
        self.display_image(f'{self.input_directory}/Horizontal_Saccade.png')

    def show_smooth_circle(self):
        self.display_image(f'{self.input_directory}/Smooth_Circle.png')

    def show_smooth_vertical(self):
        self.display_image(f'{self.input_directory}/Smooth_Vertical.png')

    def show_smooth_horizontal(self):
        self.display_image(f'{self.input_directory}/Smooth_Horizontal.png')

    def show_text_reading(self):
        self.text_reading_shown_flag = True
        self.result_canvas.plot_data(
            (self.text_reading_gaze_data['L_Text_Reading'][:, 0], self.text_reading_gaze_data['L_Text_Reading'][:, 1]),
            (self.text_reading_gaze_data['R_Text_Reading'][:, 0], self.text_reading_gaze_data['R_Text_Reading'][:, 1])
        )
        self.result_canvas.canvas_to_image()

    def display_image(self, image_path):
        """Display an image in the result canvas."""
        self.result_canvas.delete("all")
        image = Image.open(image_path)
        image = image.resize((self.result_canvas.winfo_width(), self.result_canvas.winfo_height()), Image.ANTIALIAS)
        photo_image = ImageTk.PhotoImage(image)
        self.result_canvas.create_image(self.result_canvas.winfo_width() // 2, self.result_canvas.winfo_height() // 2, anchor="center", image=photo_image)
        self.result_canvas.image = photo_image

    def exit_results(self):
        self.controller.show_home()

class Test_Routine_Canvas(tk.Canvas):
    '''
    Class to represent the "Main Canvas" of the application. Hosts the ball
    '''
    def __init__(self, master, controller):
        tk.Canvas.__init__(self, master)
        self.controller = controller
        self.config(height=controller.height, width=controller.width, bg="black")

@dataclass
class UnscaledTextData:
    x1: int
    y1: int
    width: int
    height: int
    text: str
class TextReadingResultsCanvas(tk.Canvas):
    def __init__(self, master, output_dir, rootx, rooty, padding=25, **kwargs):
        """
        A Canvas subclass that draws grids, text, and eye points,
        sized/scaled based on the widget's width/height.
        """
        super().__init__(master, **kwargs)

        self.padding = padding
        self.text_data = []
        self.output_dir = output_dir
        self.rootx = rootx
        self.rooty = rooty

        # Will store data for drawn text, points, etc.
        self.left_eye_point = None
        self.right_eye_point = None
        self.text_lines = []

        # Internal usage
        self.width = 1
        self.height = 1
        self.grid_interval = 0.2

        # Bind the <Configure> event so we can track canvas size changes
        self.bind("<Configure>", self.on_resize)

        # Initialize
        self.total_questions = 0
        self.total_correct = 0
        self.user_answers = []
        self.grade = 0
        self.configure_screen_attributes()

    def configure_screen_attributes(self):
        """
        Equivalent to your old method: set up initial width/height
        or any other screen attributes needed.
        """
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        # Example: To make it fullscreen, if needed (commented out):
        # self.master.attributes("-fullscreen", True)

    def on_resize(self, event):
        """
        Handle the resize event: store new width/height, then redraw.
        """
        self.width = event.width
        self.height = event.height
        # self.redraw()

    def redraw(self):
        """
        Clear the canvas, then redraw all elements.
        """
        self.delete("all")
        self.config(bg="white")
        self.draw_grid()
        self.draw_points()
        self.draw_text()
        self.draw_score(self.total_questions, self.total_correct)
        self.draw_legend()
        self.draw_title("Text_Reading")

    def draw_grid(self):
        """Draw a grid with x and y scales at specified intervals."""
        self.delete("grid")  # Clear any existing grid lines by tag
        TEXT_PADDING = 5

        # Draw vertical lines
        num_steps = int(1 / self.grid_interval) + 1
        for i in range(num_steps):
            x = self.padding + i * self.grid_interval * (self.width - 2 * self.padding)
            self.create_line(x, self.padding, x, self.height - self.padding, fill='gray', tags="grid")
            self.create_text(x, self.height - self.padding + TEXT_PADDING, 
                             text=f"{i * self.grid_interval :.1f}", 
                             anchor='n', tags="grid")

        # Draw horizontal lines
        for i in range(num_steps):
            y = self.height - (self.padding + i * self.grid_interval * (self.height - 2 * self.padding))
            self.create_line(self.padding, y, self.width - self.padding, y, fill='gray', tags="grid")
            self.create_text(self.padding - TEXT_PADDING, y, 
                             text=f"{i * self.grid_interval :.1f}", 
                             anchor='e', tags="grid")

    def find_font_size(self, text, width, font_family="Arial", weight="bold"):
        """
        Simple binary search for largest font size that fits within 'width' pixels.
        """
        low, high = 1, 100
        best_size = low

        while low <= high:
            mid = (low + high) // 2
            test_font = font.Font(family=font_family, size=mid, weight=weight)
            text_width = test_font.measure(text)
            
            if text_width <= width:
                best_size = mid
                low = mid + 1
            else:
                high = mid - 1

        return best_size

    def draw_text(self):
        """
        Draw text onto the canvas at scaled positions.
        """
        got_font_size = False
        for text_data in self.text_data:
            # Only calculate font size once per draw cycle (assuming same text width).
            if not got_font_size:
                # Scale the text's desired width to the canvas
                scaled_width = text_data.width * self.width
                font_size = self.find_font_size(text_data.text, scaled_width)
                got_font_size = True

            # Calculate scaled center
            x_centre_scaled = int(text_data.x1 * self.width) + (text_data.width * self.width) / 2
            y_centre_scaled = int(text_data.y1 * self.height) - (text_data.height * self.height) / 2

            # Ensure at least size=1
            font_size = max(1, font_size)

            # Draw text
            self.create_text(
                x_centre_scaled,
                y_centre_scaled,
                text=text_data.text,
                font=("Arial", font_size, "bold"),
                justify='center'
            )

    def plot_data(self, left_eye_point, right_eye_point):
        """
        Store new data points, then redraw everything.
        """
        self.left_eye_point = left_eye_point
        self.right_eye_point = right_eye_point
        self.redraw()

    def scale_point(self, point):
        """
        Convert normalized (0-1) coordinates to canvas pixels.
        Invert y because in typical computer graphics, y increases downward.
        """
        x = self.padding + point[0] * (self.width - 2 * self.padding)
        y = self.height - (self.padding + point[1] * (self.height - 2 * self.padding))
        return x, y

    def draw_points(self):
        """
        Draw separate eye points.
        """
        if self.left_eye_point:
            for x,y in zip(self.left_eye_point[0], self.left_eye_point[1]):
                left_eye = self.scale_point((x, y))
                self.create_text(left_eye[0], left_eye[1], text='•', font=("Arial", 12), fill='red')
        
        if self.right_eye_point:
            for x, y in zip(self.right_eye_point[0], self.right_eye_point[1]):
                right_eye = self.scale_point((x,y))
                self.create_text(right_eye[0], right_eye[1], text='•', font=("Arial", 12), fill='blue')

    def draw_legend(self):
        """
        Draw a legend in the top-right corner of the canvas.
        """
        self.create_text(self.width - self.padding, self.padding, text='Legend:', 
                         anchor='ne', font=("Arial", 10, "bold"))
        self.create_text(self.width - self.padding, self.padding + 20, 
                         text='• Left Eye', anchor='ne', font=("Arial", 10), fill='red')
        self.create_text(self.width - self.padding, self.padding + 40, 
                         text='• Right Eye', anchor='ne', font=("Arial", 10), fill='blue')
        
    def draw_score(self, total_questions:int, answers_right:int):
        self.create_text(self.padding, self.padding, text=f'Score: {answers_right}/{total_questions}', 
                         anchor='nw', font=("Arial", 10, "bold"))

    def draw_title(self, title):
        """
        Draw a title at the top-center of the canvas.
        """
        self.create_text(
            self.width / 2,
            self.padding / 2,
            text=title,
            font=("Arial", 16, "bold"),
            anchor='center'
        )

    def canvas_to_image(self):
        x = self.rootx + self.winfo_x()
        y = self.rooty + self.winfo_y()
        x1 = x + self.winfo_width()
        y1 = y + self.winfo_height()
        self.update_idletasks() #make sure canvas is drawn
        img = ImageGrab.grab((x, y, x1, y1))
        img.save(f"{self.output_dir}\\Text_Reading.png", "png")

    def parse_excel(self, path):
        # reset data
        self.total_questions = 0
        self.total_correct = 0
        self.user_answers = []
        self.grade = 0
        self.text_data = []
        try:
            xlsx = pd.ExcelFile(path)
            df = pd.read_excel(xlsx, 'ScreenConfig')
            screen_width, screen_height = df['Width'][0], df['Height'][0]
            
            df2 = pd.read_excel(xlsx, 'Text_Reading')
            font_size = int(df2['Font_Size'][0])
            text_lines = df2['Text'][0].split("'")
            self.full_text = " ".join(text_lines)

            x_data = df2['X'].dropna()
            y_data = df2['Y'].dropna()

            first_point = True
            i = 0
            for x, y in zip(x_data, y_data):
                if first_point:
                    (x1, y1) = (x / screen_width, (y + font_size * 0.5) / screen_height)
                    first_point = False
                else:
                    first_point = True
                    (x2, y2) = (x / screen_width, (y - font_size * 0.5) / screen_height)
                    text_width, text_height = abs(x2 - x1), abs(y2 - y1)
                    self.text_data.append(
                        UnscaledTextData(
                            x1, y1, text_width, text_height, text_lines[i]
                        )
                    )
                    i += 1

            # get score
            self.total_questions = df2['question'].count()
            self.total_correct = df2['user_answer'].eq(df2['correct_answer']).sum()
            self.user_answers = df2['user_answer'].dropna().tolist()
            self.grade = int(df2['grade'][0])
            return True
        except Exception as e:
            traceback.print_exc()
            return False


