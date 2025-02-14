'''
EYEfollow 1.1
Application Class
Gian Favero, Steven Caro and Joshua Picchioni
2024
'''

# Python Imports
from enum import Enum
import os
import sys
from time import sleep
import ctypes
import traceback

# Module Imports
import pygetwindow as gw
import tkinter as tk
from tkinter.constants import CENTER
from tkinter.messagebox import *
from custom_tk import custom_askstring

# Project Imports
from testroutine import Test_Routine, Routine_State
from frames import Home_Screen, Test_Routine_Canvas, Results_Frame, QuestionsFrame
from config import load_config_files, get_data_output_path

# Set resolution for screen
ctypes.windll.shcore.SetProcessDpiAwareness(1)

# Window title
window_title = "EYEfollow, 2024"
class Application(tk.Tk):

    class CURRENT_FRAME(Enum):
        HOME      = 1
        EYE_TEST  = 2
        COUNTDOWN = 3
        RESULTS   = 4
        QUESTIONS = 5
    
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title(window_title)

        # load config
        load_config_files()
        
        self.path = get_data_output_path()

        # If no folder, make it
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        
        # self.ignore_popup = True if sys.argv[2] == 'true' else False
        self.ignore_popup = False
        
        # Create container for application
        self.container = self.configure_container()

        # Configure screen/window attributes
        self.configure_screen_attributes()
        self.EYEfollow_window = gw.getWindowsWithTitle(window_title)[0]
        self.gazepoint_window = gw.getWindowsWithTitle("Gazepoint")[0]

        # Configure key bindings
        self.configure_binds()

        # Create the prompt button array
        self.activeButtons = {
            "Vertical_Saccade": False,
            "Horizontal_Saccade": False,
            "Smooth_Circle": False,
            "Smooth_Vertical": False,
            "Smooth_Horizontal": False,
            "Text_Reading": False,
        }

        self.frame = Home_Screen(master=self.container, controller=self)
        self.test_routine_canvas = Test_Routine_Canvas(master=self.container, controller=self)
        self.test_routine = Test_Routine(self, self.test_routine_canvas, self.ignore_popup)
        self.results_frame = Results_Frame(master=self.container, controller=self, input_directory=self.path)

        # Show the home screen
        self.show_home()

        self.update_idletasks()

        
    def configure_container(self):
        '''
        Define the container and grid of the application
        '''
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        return container

    def configure_screen_attributes(self):
        '''
        Configure the sizing and attributes of the screen window
        '''
        self.attributes("-fullscreen", True)
        self.resizable(False, False)
        self.update_idletasks()
        self.width = self.winfo_width()
        self.height = self.winfo_height()

    def configure_binds(self):
        '''
        Set up key bindings for program
        '''
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)
        self.bind("<q>", self.quit_routine)
        
    def toggle_fullscreen(self, event=None):
        '''
        Toggle window size to fullscreen
        '''
        self.attributes("-fullscreen", True)
        self.width = self.winfo_width()
        self.height = self.winfo_height()

    def end_fullscreen(self, event=None):
        '''
        Toggle window size to minimized
        '''
        self.attributes("-fullscreen", False)
        self.state("zoomed")
        self.config(cursor="arrow")
        self.width = self.winfo_width()
        self.height = self.winfo_height()
    
    def show_canvas(self, canvas: tk.Canvas, current_frame: CURRENT_FRAME):
        '''
        Raise the Test Routine Canvas to the top of the stack and start test routine
        '''
        canvas.place(relx=0.5, rely=0.5, anchor=CENTER)
        self.canvas = canvas
        tk.Misc.lift(canvas)
        self.current_frame = current_frame
        self.update_idletasks()

    def show_home(self):
        '''
        Raise the Home Screen to the top of the stack
        '''
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.tkraise()
        self.current_frame = self.CURRENT_FRAME.HOME

    def quit_routine(self, event=None):
        '''
        End a vision test routine prematurely
        '''
        if self.current_frame == self.CURRENT_FRAME.EYE_TEST:
            answer = askyesno(title='Quit Routine', message='Are you sure you want to quit?')
            if answer:
                self.frame.tkraise()
                self.config(cursor="arrow")
                self.test_routine.cancel()

                self.reset_buttons()

                # Close Gazepoint
                os.system("TASKKILL /IM Gazepoint.exe /F")
                print("Gazepoint closed.")
                
                self.current_frame = self.CURRENT_FRAME.HOME

    
    def routine_finished(self, event=None, show_popup=True):
        '''
        Define exit behaviour once the selected vision therapy tests have been completed
        '''
        if show_popup is True:
            answer = showinfo(title="Completion", message="Eye Test Complete")
        else:
            answer = True

        if answer:
            self.frame.tkraise() 

            self.activeButtons = {"Vertical_Saccade" : True, "Horizontal_Saccade" : True, 
                                "Smooth_Circle" : True,    "Smooth_Vertical" : True, 
                                "Smooth_Horizontal" : True, "Text_Reading" : True}
            
            # Reset the home screen buttons
            self.reset_buttons()

            # Return the arrow cursor
            self.config(cursor="arrow")

            self.current_frame = self.CURRENT_FRAME.HOME
        
    def activate_button(self, button_name):
        '''
        Activate a button on the prompt menu
        '''
        if self.activeButtons[button_name] is False:
            self.activeButtons[button_name] = True
        else:
            self.activeButtons[button_name] = False

    def reset_buttons(self):
        '''
        Reset the prompt menu buttons
        '''
        for key in self.activeButtons.keys():
            self.activeButtons[key] = False
        
        self.frame.reset_buttons()
    
    def show_questions(self, questions):
        """
        Switch to the QuestionsFrame to display questions.
        """
        # self.test_routine_canvas.grid_forget()
        self.questions_frame = QuestionsFrame(master=self.container, controller=self, questions=questions)
        self.questions_frame.grid(row=0, column=0, sticky="nsew")
        self.questions_frame.tkraise()
        self.current_frame = self.CURRENT_FRAME.QUESTIONS

    def restart_gazepoint(self):
        """
        Restart the Gazepoint application.
        """
        try:
            # Kill the Gazepoint process if it is running
            os.system("TASKKILL /IM Gazepoint.exe /F")
            sleep(2)
            
            # Start the Gazepoint application
            os.startfile(r'C:/Program Files (x86)/Gazepoint/Gazepoint/bin64/Gazepoint.exe')
            sleep(5)
            
            # Get the Gazepoint window
            gazepoint_window = gw.getWindowsWithTitle("Gazepoint")
            if gazepoint_window:
                gazepoint_window = gazepoint_window[0]
                print("Gazepoint restarted successfully.")
            else:
                print("Gazepoint window not found.")
        except Exception as e:
            print(f"Failed to restart Gazepoint: {e}")


    def handle_question_results(self, results):
        """
        Handle results after questions are answered.
        """
        # Display results or move to the next test
        for result in results:
            print(f"Q: {result['question']}, User: {result['user_answer']}, Correct: {result['correct_answer']}")
        self.test_routine.transition_to_next_test(results)

    def show_results(self):
        """
        Show the Results Frame.
        """
        self.results_frame.grid(row=0, column=0, sticky="nsew")
        self.results_frame.tkraise()
        self.current_frame = self.CURRENT_FRAME.RESULTS

    def create_test_routine(self):
        '''
        Create the array of routines selected for the current sequence of vision tests
        '''
        # Bring calibration window to the forefront
        while True:
            activate_gazepoint(self.gazepoint_window)

            while gw.getActiveWindowTitle() == "Gazepoint Control x64" and not None:
                sleep(10e-2)

            # check if can communicate with gazepoint
            retval = self.test_routine.tracker.test_collection()
            if retval is True:
                break
            else:
                showerror("Error", "Error attempting to communicate with Gazepoint. Restarting Gazepoint.")
                print("Failed to communicate with eyetracker. Restarting")
                self.restart_gazepoint()


        invalid_windows_file_characters = ['/','\\',':','*','?','"','<','>','|']
        # Get participant's name
        if self.ignore_popup is not True:
            participant_name = custom_askstring("Input Name", f"Input Participant's Name{30*' '}", self, invalid_windows_file_characters)
        else:
            participant_name = ''

        if participant_name is None:
            self.reset_buttons()
            self.EYEfollow_window.activate()
        else:
            if participant_name == '':
                participant_name = "Sample_Participant"

            # Activate EYEfollow window
            self.EYEfollow_window = gw.getWindowsWithTitle(window_title)[0]
            try:
                self.EYEfollow_window.activate()
            except Exception as e:
                print(f"Error switching back to eyefollow window: {e}")

            # Hide mouse
            self.config(cursor="none")

            # Display the test routine canvas 
            self.show_canvas(self.test_routine_canvas, self.CURRENT_FRAME.EYE_TEST)

            # Add the selected test options to a list
            tests = []
            for key, item in self.activeButtons.items():
                if item is True:
                    tests.append(key)
            
            # Pass the participant name and list to the Test Routine and update the test_routine state
            self.test_routine.participant_name = participant_name
            self.test_routine.test_names = iter(tests)
            self.test_routine.current_test = next(self.test_routine.test_names)
            self.test_routine.state = Routine_State.update_test
    
    def show_test_routine_canvas(self):
        self.show_canvas(self.test_routine_canvas, self.CURRENT_FRAME.EYE_TEST)


def activate_gazepoint(window='empty'):
    # Check if window was accidentally closed
    gazepoint_window = None if "Gazepoint Control x64" not in gw.getAllTitles() else window

    for attempts in range(3):
        try:
            if gazepoint_window is None:
                os.startfile('C:/Program Files (x86)/Gazepoint/Gazepoint/bin64/Gazepoint.exe')
                sleep(2)
                gazepoint_window = gw.getWindowsWithTitle("Gazepoint")[0]
            elif gazepoint_window == 'empty':
                gazepoint_window = gw.getWindowsWithTitle("Gazepoint")[0]
                gazepoint_window.activate()
            else:
                gazepoint_window.activate()
            sleep(0.2)
            # gazepoint active, try sending messages
            break
        except:
            traceback.print_exc()
    if attempts >= 2 and gazepoint_window is None:
        print("Failed to activate gazepoint 3+ times in a row.")
    return gazepoint_window

if __name__ == '__main__':

    # Start Gazepoint Control
    try:
        activate_gazepoint()
        sleep(2)
    except:
        traceback.print_exc()

    app = Application()
    app.mainloop()

    # Close Gazepoint Control
    try:
        os.system("TASKKILL /IM Gazepoint.exe")
    except:
        traceback.print_exc()
