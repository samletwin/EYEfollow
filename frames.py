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
        self.start_b.grid(row=3, column=0, columnspan = 9, pady=75)
        self.results_b.grid(row=5, column=0, columnspan = 9, pady=75)

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
                self.SH_b.configure(bg="#adffab")
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
        
class Results_Frame(tk.Frame):
    def __init__(self, master, controller, input_directory):
        super().__init__(master)
        self.controller = controller
        self.input_directory = input_directory
        self.configure(bg="white")

        # Dropdown to select Excel file
        self.file_label = tk.Label(self, text="Select Excel File:", bg="white")
        self.file_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.file_dropdown = ttk.Combobox(self)
        self.file_dropdown['values'] = self.get_excel_files()
        self.file_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Confirm button to select file
        self.confirm_button = tk.Button(self, text="Confirm", command=self.confirm_file_selection)
        self.confirm_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        # Buttons for different result types (initially disabled)
        self.VS_button = tk.Button(self, text='Vertical Saccade', command=self.show_vertical_saccade, state='disabled')
        self.HS_button = tk.Button(self, text='Horizontal Saccade', command=self.show_horizontal_saccade, state='disabled')
        self.SC_button = tk.Button(self, text='Smooth Circle', command=self.show_smooth_circle, state='disabled')
        self.SV_button = tk.Button(self, text='Smooth Vertical', command=self.show_smooth_vertical, state='disabled')
        self.SH_button = tk.Button(self, text='Smooth Horizontal', command=self.show_smooth_horizontal, state='disabled')
        self.TR_button = tk.Button(self, text='Text Reading', command=self.show_text_reading, state='disabled')

        self.VS_button.grid(row=1, column=0, padx=10, pady=5)
        self.HS_button.grid(row=2, column=0, padx=10, pady=5)
        self.SC_button.grid(row=3, column=0, padx=10, pady=5)
        self.SV_button.grid(row=4, column=0, padx=10, pady=5)
        self.SH_button.grid(row=5, column=0, padx=10, pady=5)
        self.TR_button.grid(row=6, column=0, padx=10, pady=5)

        # Canvas to display results
        self.result_canvas = tk.Canvas(self, bg="gray")
        self.result_canvas.grid(row=1, column=1, rowspan=6, padx=10, pady=5, sticky="nsew")

        # Exit button to go back to home screen
        self.exit_button = tk.Button(self, text="Exit", command=self.exit_results)
        self.exit_button.grid(row=7, column=0, columnspan=2, pady=10)

        # Configure row and column weights
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

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
        file_name, file_extension = os.path.splitext(selected_file)
        file_name_gt = file_name + '_GT' + file_extension
        file_path_gt = os.path.join(self.input_directory, file_name_gt)
        enabled_buttons = process_excel_file(file_path, file_path_gt)

        # Enable buttons based on the result of file processing
        self.VS_button.config(state='normal' if enabled_buttons.get('Vertical_Saccade') else 'disabled')
        self.HS_button.config(state='normal' if enabled_buttons.get('Horizontal_Saccade') else 'disabled')
        self.SC_button.config(state='normal' if enabled_buttons.get('Smooth_Circle') else 'disabled')
        self.SV_button.config(state='normal' if enabled_buttons.get('Smooth_Vertical') else 'disabled')
        self.SH_button.config(state='normal' if enabled_buttons.get('Smooth_Horizontal') else 'disabled')
        self.TR_button.config(state='normal' if enabled_buttons.get('Text_Reading') else 'disabled')

        # Display message if no data is available
        if not any(enabled_buttons.values()):
            self.result_canvas.delete("all")
            self.result_canvas.create_text(self.result_canvas.winfo_width() // 2, self.result_canvas.winfo_height() // 2, text="No data present", fill="black", font=("Helvetica", 16))

    def show_vertical_saccade(self):
        self.display_image('images2/Vertical_Saccade.png')

    def show_horizontal_saccade(self):
        self.display_image('images2/Horizontal_Saccade.png')

    def show_smooth_circle(self):
        self.display_image('images2/Smooth_Circle.png')

    def show_smooth_vertical(self):
        self.display_image('images2/Smooth_Vertical.png')

    def show_smooth_horizontal(self):
        self.display_image('images2/Smooth_Horizontal.png')

    def show_text_reading(self):
        self.display_image('images2/Text_Reading.png')

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

