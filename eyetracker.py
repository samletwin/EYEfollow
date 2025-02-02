'''
EYEfollow 1.1
EyeTracker Data Management Class 
Gian Favero and Steven Caro
2023
'''

# Python Imports
import os
from time import sleep

# Module Imports
from open_gaze import EyeTracker
import pandas as pd

class EyeTracker_DM(EyeTracker):
    def __init__(self, master):
        super().__init__()
        self.master = master
        self.tracker = EyeTracker()
        self.tracker_data = None
        self.dfs = {}
        self.GT_dfs = {}

    def set_screen_cfg(self, key, screen_cfg_data):
        self.GT_dfs[key] = pd.DataFrame(screen_cfg_data)
    
    def start_collection(self):
        '''
        Starts eye tracker data collection
        '''
        try:
            self.tracker_data = list[tuple[float, str, dict[str, str]]]()
            self.send_data        = True
            self.send_pupil_left  = True
            self.send_pupil_right = True
            self.send_pog_left    = True
            self.send_pog_right   = True
            self.send_time        = True
            print(f"Started collecting data: {self.master.current_test}")
        except:
            print('FAILED TO START')
            self.start_collection()
    
    def stop_collection(self):
        '''
        Stops eye tracker data collection, serializes it, and then formats into a pd dataframe
        '''
        try:
            self.send_data        = False
            self.send_pupil_left  = False
            self.send_pupil_right = False
            self.send_pog_left    = False
            self.send_pog_right   = False
            self.send_time        = False
            print(f"Finished collecting data: {self.master.current_test}")
        except:
            print("FAILED TO STOP")
            self.stop_collection()
        while True:
            sleep(1e-2)
            if self.read_msg_async() is None:
                break

        if self.master.current_test != "Done":
            self.tracker_data = self.serialize_tracker_data(self.tracker_data)
            self.dfs[self.master.current_test]=pd.DataFrame(self.tracker_data)
            self.GT_dfs[self.master.current_test]=pd.DataFrame(dict([(k, pd.Series(v)) for k, v in self.master.GTdata[self.master.current_test].items()])) #handles arrays of diff length

    def serialize_tracker_data(self, data: list[tuple[float, str, dict[str, str]]]) -> str:
        '''
        Organizes the raw data from the GazePoint eye tracker into column sorted arrays
        '''
        result={}
        for key in [
                        "TIME",
                        "LPOGX", "LPOGY", "LPOGV",            # Sent by send_pog_left
                        "RPOGX", "RPOGY", "RPOGV",            # Sent by send_pog_right
                        "LPCX", "LPCY", "LPD", "LPS", "LPV",  # Sent by send_pupil_left
                        "RPCX", "RPCY", "RPD", "RPS", "RPV",  # Sent by send_pupil_right
                    ]:
                        result[key] = []

        for contents in data:
            try:
                # Only taking entries with REC and TIME filters out incomplete data tuple entries
                if 'REC' in contents and 'TIME' in contents[2].keys():
                    for key in [
                            "TIME",
                            "LPOGX", "LPOGY", "LPOGV",            # Sent by send_pog_left
                            "RPOGX", "RPOGY", "RPOGV",            # Sent by send_pog_right
                            "LPCX", "LPCY", "LPD", "LPS", "LPV",  # Sent by send_pupil_left
                            "RPCX", "RPCY", "RPD", "RPS", "RPV",  # Sent by send_pupil_right
                            ]: 

                            result[key].append(float(contents[2][key]) if key in contents[2] else '')
            except:
                print(contents) # TODO get to the bottom of this (if program gets here, no data is written)
                
        return result

    def export_data(self):
        '''
        Exports the pd dataframe to an Excel file
        '''
        path = self.master.master.path
        if not os.path.exists(path):
            os.makedirs(path)

        #TODO: fix this  
        self.GT_dfs["Text_Reading"]=pd.DataFrame(dict([(k, pd.Series(v)) for k, v in self.master.GTdata["Text_Reading"].items()])) #handles arrays of diff length
        
        with pd.ExcelWriter(f"{path}/{self.master.participant_name}_GT.xlsx") as writer:
            for key in self.master.GTdata.keys():
                self.GT_dfs[key].to_excel(writer, sheet_name=key)

        with pd.ExcelWriter(f"{path}/{self.master.participant_name}.xlsx") as writer:
            for key in self.dfs.keys():
                self.dfs[key].to_excel(writer, sheet_name=key)
        self.dfs = {} # reset once exporting