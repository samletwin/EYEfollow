'''
EYEfollow 1.1
Home Screen Class
Gian Favero, Steven Caro and Joshua Picchioni
2024
'''

import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk
from tkinter.messagebox import *
import os
from processing import process_excel_file
from images_to_pdf import images_to_pdf
import threading

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
        self.configure(bg="white", cursor="arrow")
        self.screen_width = self.winfo_screenwidth()

        self.selected_button_index = {}
        self.create_question_widgets()

    def create_question_widgets(self):
        self.current_row = 0

        # Store state for answers
        self.selected_answers = {}  # To track selected answers for each question
        self.correct_answers = {}  # To store correct answers
        self.option_widgets = {}  # To store option widgets for highlighting

        for i, question in enumerate(self.questions):
            question_text = question["message"]
            options = question["options"]
            correct_answer = question["answer"]

            # Save correct answer for the question
            self.correct_answers[i] = correct_answer
            self.option_widgets[i] = []  # Initialize list for storing option widgets

            # Display question text
            tk.Label(
                self, text=f"Q{i+1}: {question_text}", font=("Arial", 16, "bold"),
                bg="white", anchor="center"
            ).grid(row=self.current_row, column=0, pady=(20 if i == 0 else 10, 10), sticky="ew")
            self.current_row += 1

            # Create a frame for radio buttons
            options_frame = tk.Frame(self, bg="white")
            options_frame.grid(row=self.current_row, column=0, pady=10, sticky="ew")

            # Center options
            options_frame.grid_columnconfigure(0, weight=1)

            # Create buttons for options with callbacks
            for option in options:
                radio_button = tk.Radiobutton(
                    options_frame,
                    text=option,
                    value=option,
                    variable=tk.IntVar(),
                    command=lambda q=i, opt=option: self.store_answer(q, opt),
                    bg="white",
                    font=("Arial", 14),
                    cursor="arrow"
                )
                radio_button.pack(side="left", fill="x",padx=10)
                self.option_widgets[i].append(radio_button)  # Store the widget for later
            self.current_row += 1

        # Submit button
        self.submit_button = tk.Button(
            self, text="Submit", command=self.submit_answers, bg="#adffab", cursor="arrow"
        )
        self.submit_button.grid(row=self.current_row, column=0, pady=20, sticky="ew")

        # Score label
        self.score_label = tk.Label(self, text="", font=("Arial", 16), bg="white", fg="black")
        self.score_label.grid(row=self.current_row + 1, column=0, pady=10, sticky="ew")


    def store_answer(self, question_index, selected_option):
        self.selected_answers[question_index] = selected_option

    def submit_answers(self):
        self.submit_button.configure(state="disabled")
        correct_count = 0

        # Compare selected answers with correct answers and highlight
        for i, correct_answer in self.correct_answers.items():
            selected_answer = self.selected_answers.get(i, None)  # Get the selected answer or None

            # Highlight options for the current question
            for radio_button in self.option_widgets[i]:
                if radio_button["text"] == correct_answer:
                    radio_button.configure(bg="lightgreen")  # Correct answer
                elif radio_button["text"] == selected_answer:
                    radio_button.configure(bg="red")  # Incorrect selection

            # Count correct answers
            if selected_answer == correct_answer:
                correct_count += 1

        # Display the score
        self.score_label.config(text=f"Score: {correct_count}/{len(self.questions)}")
        self.current_row+=1
        tk.Button(
            self, text="Retry test?", command=self.retry, bg="#adffab", cursor="arrow"
        ).grid(row=self.current_row, column=0, padx=10, sticky="w")
        tk.Button(
            self, text="Continue", command=self.handle_results, bg="#adffab", cursor="arrow"
        ).grid(row=self.current_row, column=1, padx=10, sticky="e")

    def handle_results(self):
        results = []

        # Iterate through the questions and user answers
        for i, correct_answer in self.correct_answers.items():
            user_answer = self.selected_answers.get(i, None)  # Get the selected answer or None
            is_correct = user_answer == correct_answer

            # Append the results for each question
            results.append({
                "question": self.questions[i]["message"],
                "user_answer": user_answer if user_answer else "No Answer",
                "correct_answer": correct_answer,
                "is_correct": is_correct
            })

        # Process results further if needed (e.g., send to controller)
        self.controller.handle_question_results(results)

    def retry(self):
        self.controller.show_test_routine_canvas()
        self.controller.test_routine.reading_main()


class Results_Frame(tk.Frame):
    def __init__(self, master, controller, input_directory):
        super().__init__(master)
        self.controller = controller
        self.input_directory = input_directory
        self.configure(bg="white")

        self.enabled_buttons = {}
        self.image_paths = []
        self.file_name = ''

        # Dropdown to select Excel file
        self.file_label = tk.Label(self, text="Select Excel File:", bg="white")
        self.file_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.file_dropdown = ttk.Combobox(self, state="readonly")
        self.file_dropdown['values'] = self.get_excel_files()
        self.file_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Confirm button to select file
        self.confirm_button = tk.Button(self, text="Confirm", command=self.confirm_file_selection)
        self.confirm_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        # button to export results to pdf
        self.to_pdf_button = tk.Button(self, text="Export to PDF", 
                                       command=lambda: images_to_pdf(self.image_paths, f"{self.input_directory}/{self.file_name}.pdf", self.file_name), state='disabled')
        self.to_pdf_button.grid(row=0, column=3, padx=10, pady=10, sticky="w")


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
        self.result_canvas = tk.Canvas(self, bg="gray")
        self.result_canvas.grid(row=1, column=1, rowspan=6, padx=10, pady=5, sticky="nsew")

        # Exit button to go back to home screen
        self.exit_button = tk.Button(self, text="Exit", command=self.exit_results)
        self.exit_button.grid(row=7, column=0, columnspan=3, padx=20, pady=10, sticky="ew")

        # Configure row and column weights
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.animate_text = False
        self.animate_counter = 0

    def tkraise(self, aboveThis=None):
        super().tkraise(aboveThis)
        # update excel files
        self.file_dropdown['values'] = self.get_excel_files()

    def get_excel_files(self):
        """Retrieve a list of Excel files from the input directory."""
        return [f for f in os.listdir(self.input_directory) if f.endswith('.xlsx') and not f.endswith('_GT.xlsx')]

    def confirm_file_selection(self):
        """Process the selected Excel file and enable buttons based on data availability."""
        selected_file = self.file_dropdown.get()
        if not selected_file:
            return

        file_path = os.path.join(self.input_directory, selected_file)
        self.file_name, file_extension = os.path.splitext(selected_file)
        file_name_gt = self.file_name + '_GT' + file_extension
        file_path_gt = os.path.join(self.input_directory, file_name_gt)
        self.start_processing(file_path, file_path_gt)

    def animate_text_func(self):
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
            self.enabled_buttons = process_excel_file(file_path, file_path_gt, self.input_directory)
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
        self.display_image(f'{self.input_directory}/Text_Reading.png')

    def display_image(self, image_path):
        """Display an image in the result canvas."""
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

