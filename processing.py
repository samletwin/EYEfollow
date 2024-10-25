import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def gzclean(gxin, gyin, flag, time):
    """
    Cleans the data based on the flag and time conditions.
    """
    idx = np.where((flag != 0) & (time > 5))[0]
    gxout = gxin[idx]
    gyout = gyin[idx]
    timeout = time[idx]
    return gxout, gyout, timeout

def process_participant_data(file_path, sheets):
    """
    Processes a single participant's pupil center data based on their file path.
    """
    pupil_data = {}
    for sheet in sheets:
        file_data = pd.read_excel(file_path, sheet_name=sheet).to_numpy()
        time = file_data[:, 1]
        flagL = file_data[:, 12]
        flagR = file_data[:, 17]
        Lx = file_data[:, 8]
        Ly = file_data[:, 9]
        Rx = file_data[:, 13]
        Ry = file_data[:, 14]

        Lx_clean, Ly_clean, timeL_clean = gzclean(Lx, Ly, flagL, time)
        Rx_clean, Ry_clean, timeR_clean = gzclean(Rx, Ry, flagR, time)

        pupil_data[f'L_{sheet}'] = np.column_stack((Lx_clean, Ly_clean, timeL_clean))
        pupil_data[f'R_{sheet}'] = np.column_stack((Rx_clean, Ry_clean, timeR_clean))

    return pupil_data

def process_gaze_data(file_path, sheets):
    """
    Processes gaze data for a single participant based on their file path.
    """
    gaze_data = {}
    for sheet in sheets:
        file_data = pd.read_excel(file_path, sheet_name=sheet).to_numpy()
        time = file_data[:, 1]
        flagL = file_data[:, 4]
        flagR = file_data[:, 7]
        Lx = file_data[:, 2]
        Ly = file_data[:, 3]
        Rx = file_data[:, 5]
        Ry = file_data[:, 6]

        Lx_clean, Ly_clean, timeL_clean = gzclean(Lx, Ly, flagL, time)
        Rx_clean, Ry_clean, timeR_clean = gzclean(Rx, Ry, flagR, time)

        gaze_data[f'L_{sheet}'] = np.column_stack((Lx_clean, Ly_clean, timeL_clean))
        gaze_data[f'R_{sheet}'] = np.column_stack((Rx_clean, Ry_clean, timeR_clean))

    return gaze_data

def process_ground_truth_data(file_path, sheets):
    """
    Processes ground truth data for a single participant based on their file path.
    """
    gt_data = {}
    # get screenconfig data
    screen_cfg = pd.read_excel(file_path, sheet_name='ScreenConfig').to_numpy()
    screen_width = screen_cfg[0, 1]
    screen_height = screen_cfg[0, 2]
    for sheet in sheets:
        file_data = pd.read_excel(file_path, sheet_name=sheet).to_numpy()
        # Replace string "NaN" values with None
        file_data = np.where(file_data == "NaN", None, file_data)

        if sheet == 'Vertical_Saccade' or sheet == 'Horizontal_Saccade':
            x = file_data[0:2, 1]
            y = file_data[0:2, 2]
        elif sheet == 'Text_Reading':
            x = file_data[0:, 1]
            y = file_data[0:, 2]
        else:
            x = file_data[0:, 2]
            y = file_data[0:, 3]

        # Handle None values to avoid issues in calculations
        x = np.array([val / screen_width if val is not None else None for val in x])
        y = np.array([val / screen_height if val is not None else None for val in y])
        gt_data[sheet] = np.column_stack((x, y))

    return gt_data

def eye_data_to_image(dataPC, dataGaze, dataGT, key, title, pathToSave=None):
    """
    Plots data for the left and right eye based on the provided data.
    """

    fig, ax = plt.subplots(1, 2, figsize=(16, 9))
    plt.suptitle(title)
    
    # Left eye plot
    line1, = ax[0].plot(dataPC[f'L_{key}'][:, 0], dataPC[f'L_{key}'][:, 1], '.', color=[0.4660, 0.6740, 0.1880], label='Pupil')
    line2, = ax[0].plot(dataGaze[f'L_{key}'][:, 0], dataGaze[f'L_{key}'][:, 1], '.', color='red', label='Gaze')
    line3, = ax[0].plot(dataGT[key][:, 0], dataGT[key][:, 1], linewidth=3, color='blue', label='Ground Truth')
    ax[0].set_title("Left eye")
    ax[0].set_xlim([0, 1])
    ax[0].set_ylim([0, 1])
    ax[0].grid(True)

    # Right eye plot
    ax[1].plot(dataPC[f'R_{key}'][:, 0], dataPC[f'R_{key}'][:, 1], '.', color=[0.4660, 0.6740, 0.1880])
    ax[1].plot(dataGaze[f'R_{key}'][:, 0], dataGaze[f'R_{key}'][:, 1], '.', color='red')
    ax[1].plot(dataGT[key][:, 0], dataGT[key][:, 1], linewidth=3, color='blue')
    ax[1].set_title("Right eye")
    ax[1].set_xlim([0, 1])
    ax[1].set_ylim([0, 1])
    ax[1].grid(True)

    # Add legend to the entire figure
    fig.legend(handles=[line1,line2,line3])
    if pathToSave is not None:
        plt.savefig(f"{pathToSave}/{key}.png", bbox_inches='tight', dpi=100)

def process_excel_file(file_path, file_path_gaze):
    """
    Process the Excel file and return a dictionary indicating which buttons should be enabled.
    Handles errors if sheets are not present by setting corresponding keys to False.
    """


    sheets = ['Vertical_Saccade', 'Horizontal_Saccade', 'Smooth_Circle', 'Smooth_Horizontal', 'Smooth_Vertical', 'Text_Reading']
    enabled_buttons = {sheet: False for sheet in sheets}
    sheets_to_remove = []
    for sheet in sheets:
        try:
            # Attempt to read the sheet from the Excel file
            file_data = pd.read_excel(file_path, sheet_name=sheet)
            # If the sheet is read successfully and contains data, enable the corresponding button
            if not file_data.empty:
                enabled_buttons[sheet] = True
        except ValueError:
            # Sheet not found, keep the button disabled (False)
            enabled_buttons[sheet] = False
            sheets_to_remove.append(sheet)
    for sheet in sheets_to_remove:
        sheets.remove(sheet)
    # Process the data using the full paths
    dataPC = process_participant_data(file_path, sheets)
    dataGaze = process_gaze_data(file_path, sheets)
    dataGT = process_ground_truth_data(file_path_gaze, sheets)

    for sheet in sheets:
        path_to_save = r'C:\Users\samle\Desktop\masters_local\EYEfollow\images2'
        eye_data_to_image(dataPC, dataGaze, dataGT, sheet, sheet, path_to_save)

    return enabled_buttons
