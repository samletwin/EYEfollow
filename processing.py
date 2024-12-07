import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
 
 
def data_windowing(time, x, y, windows):
    time_diff = time[-1] - time[0]
    w = time_diff/windows
    tW = []
    xW = []
    yW = []
    t = []
    for i in range(windows):
        start_time = time[0] + w*(i)
        stop_time = time[0] + w*(i+1)
        idx = np.where((start_time<=time) & (time<stop_time))[0]
        t = time[idx[0]:idx[-1]]
        midpoint = math.ceil(len(t)/2)
        tW.append(t[midpoint])
        xW.append(np.average(x[idx]))
        yW.append(np.average(y[idx]))
    return tW, xW, yW
 
def clustering_function(x, y, centroid1x, centroid1y, centroid2x, centroid2y):
    g0_cluster1 = np.zeros(len(x))
    g0_cluster2 = np.zeros(len(x))
 
    for i in range(len(x)):
        # euclidian distance
        distance1 = math.sqrt( (centroid1x - x[i])**2 + (centroid1y-y[i])**2 )
        distance2 = math.sqrt( (centroid2x - x[i])**2 + (centroid2y-y[i])**2 )
        # if 1 < 2, point belongs to cluster 1
        # if 1 > 2, point belongs to cluster 2
        if distance1 < distance2:
            g0_cluster1[i] = 1
        elif distance1 > distance2:
            g0_cluster2[i] = 1
   
    idx1 = np.where(g0_cluster1 == 1)[0]
    C1x = x[idx1]
    C1y = y[idx1]
    idx2 = np.where(g0_cluster2 == 1)[0]
    C2x = x[idx2]
    C2y = y[idx2]
 
    return C1x, C1y, C2x, C2y
 
def gzclean(gxin, gyin, flag, time):
    """
    Cleans the data based on the flag and time conditions.
    """
    idx = np.where((flag != 0) & (time > 5))[0]
    gxout = gxin[idx]
    gyout = gyin[idx]
    timeout = time[idx]
    return gxout, gyout, timeout


def rmse_function(x, y, xT, yT):
    x = np.array(x)    
    y = np.array(y)    
    xT = np.array(xT)    
    yT = np.array(yT)    
    return np.sqrt(np.mean((x - xT)**2 + (y - yT)**2))
 
def corr_function(x, y, xGT, yGT):
    x_corr = np.corrcoef(x, xGT)[0, 1]
    y_corr = np.corrcoef(y, yGT)[0, 1]
 
    corr_val = np.nanmean([x_corr, y_corr])
 
    return corr_val
 
def saccade_metric(eye, key, dataGaze, dataGT):
    x = dataGaze[f'{eye}_{key}'][:, 0]
    y = dataGaze[f'{eye}_{key}'][:, 1]
 
    xGT = dataGT[f'{key}'][:, 0]
    yGT = dataGT[f'{key}'][:, 1]
 
    C1x, C1y, C2x, C2y = clustering_function(x, y, xGT[0], yGT[0], xGT[1], yGT[1])
    C1rmse = rmse_function(C1x, C1y, xGT[0], yGT[0])
    C2rmse = rmse_function(C2x, C2y, xGT[1], yGT[1])
    rmse = (1 - np.average([C1rmse, C2rmse]))*100
    return round(rmse, 4)
 
def smooth_pursuit_metric(eye, key, dataGaze, dataGT):
    x = dataGaze[f'{eye}_{key}'][:, 0]
    y = dataGaze[f'{eye}_{key}'][:, 1]
    t = dataGaze[f'{eye}_{key}'][:, 2]
    xGT = dataGT[f'{key}'][:, 0]
    yGT = dataGT[f'{key}'][:, 1]
    tGT = dataGT[f'{key}'][:, 2]
 
    if len(t) >= 2:
        tGT = [t[0]+tGT_val for tGT_val in tGT]
        tW, xW, yW = data_windowing(t, x, y, 20)
        tW_GT, xW_GT, yW_GT = data_windowing(tGT, xGT, yGT, 20)
    
        rmse = (1 - rmse_function(xW, yW, xW_GT, yW_GT) )*100
        corr = corr_function(xW, yW, xW_GT, yW_GT)*100
        return round(rmse,4), round(corr, 4)
    else:
        return None, None
 
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
            t = np.zeros(len(x))
        elif sheet == 'Text_Reading':
            x = file_data[0:, 1]
            y = file_data[0:, 2]
            t = np.zeros(len(x))
        else:
            t = file_data[0:, 1]
            x = file_data[0:, 2]
            y = file_data[0:, 3]
 
        # Handle None values to avoid issues in calculations
        x = np.array([val / screen_width if val is not None else None for val in x])
        y = np.array([val / screen_height if val is not None else None for val in y])
        gt_data[sheet] = np.column_stack((x, y, t))
 
    return gt_data
 
def eye_data_to_image(dataPC, dataGaze, dataGT, key, title, pathToSave=None, plotPCData=False, text=''):
    """
    Plots data for the left and right eye based on the provided data.
    """
 
    if plotPCData is True:
        fig, ax = plt.subplots(2, 2, figsize=(16, 9))
        plt.suptitle(title)
    
        # Left eye plot
        line1, = ax[0][0].plot(dataPC[f'L_{key}'][:, 0], dataPC[f'L_{key}'][:, 1], '.', color=[0.4660, 0.6740, 0.1880], label='Pupil')
        line2, = ax[0][0].plot(dataGaze[f'L_{key}'][:, 0], dataGaze[f'L_{key}'][:, 1], '.', color='red', label='Gaze')
        line3, = ax[0][0].plot(dataGT[key][:, 0], dataGT[key][:, 1], linewidth=3, color='blue', label='Ground Truth')
        ax[0][0].set_title("Left eye")
        ax[0][0].set_xlim([0, 1])
        ax[0][0].set_ylim([0, 1])
        ax[0][0].grid(True)
    
        # Right eye plot
        ax[0][1].plot(dataPC[f'R_{key}'][:, 0], dataPC[f'R_{key}'][:, 1], '.', color=[0.4660, 0.6740, 0.1880])
        ax[0][1].plot(dataGaze[f'R_{key}'][:, 0], dataGaze[f'R_{key}'][:, 1], '.', color='red')
        ax[0][1].plot(dataGT[key][:, 0], dataGT[key][:, 1], linewidth=3, color='blue')
        ax[0][1].set_xlim([0, 1])
        ax[0][1].set_ylim([0, 1])
        ax[0][1].grid(True)
    
        # Left eye plot - pupil only
        ax[1][0].plot(dataPC[f'L_{key}'][:, 0], dataPC[f'L_{key}'][:, 1], '.', color=[0.4660, 0.6740, 0.1880])
        ax[1][0].grid(True)
    
        # Right eye plot - pupil only
        ax[1][1].plot(dataPC[f'R_{key}'][:, 0], dataPC[f'R_{key}'][:, 1], '.', color=[0.4660, 0.6740, 0.1880])
        ax[1][1].grid(True)

        # perform metrics
        if ('Saccade' in key):
            rmse_l = saccade_metric('L', key, dataGaze, dataGT)
            rmse_r = saccade_metric('R', key, dataGaze, dataGT)
            ax[0][0].set_title(f"Left eye\nRMSE={rmse_l}")
            ax[0][1].set_title(f"Right eye\nRMSE={rmse_r}")
        elif('Smooth' in key):
            rmse_l, corr_l = smooth_pursuit_metric('L', key, dataGaze, dataGT)
            rmse_r, corr_r = smooth_pursuit_metric('R', key, dataGaze, dataGT)
            ax[0][0].set_title(f"Left eye\nRMSE={rmse_l} CORR={corr_l}")
            ax[0][1].set_title(f"Right eye\nRMSE={rmse_r} CORR={corr_r}")
        else:
            ax[0][0].set_title(f"Left eye")
            ax[0][1].set_title(f"Right eye")
    else:
        fig, ax = plt.subplots(1, 2, figsize=(16, 9))
        plt.suptitle(title)
    
        # Left eye plot
        lines = []
        line2, = ax[0].plot(dataGaze[f'L_{key}'][:, 0], dataGaze[f'L_{key}'][:, 1], '.', color='red', label='Gaze')
        ax[0].set_title("Left eye")
        ax[0].set_xlim([0, 1])
        ax[0].set_ylim([0, 1])
        ax[0].grid(True)
    
        # Right eye plot
        ax[1].plot(dataGaze[f'R_{key}'][:, 0], dataGaze[f'R_{key}'][:, 1], '.', color='red')
        ax[1].set_xlim([0, 1])
        ax[1].set_ylim([0, 1])
        ax[1].grid(True)
 
        lines.append(line2)
        if (key == 'Text_Reading'):
            text_lines = text.split("\n")
            for i, axis in enumerate(ax[:2]):  # Only iterate over the first two axes
                x_gt = dataGT[key][:, 0]
                y_gt = dataGT[key][:, 1]

                for idx, (x, y) in enumerate(zip(x_gt, y_gt)):
                    if idx < len(text_lines):  # Only plot text if there’s a corresponding line
                        line_text = text_lines[idx]
                    else:
                        line_text = ""  # Leave empty if no text is available

                    bbox = axis.get_window_extent()
                    axis_width = bbox.width
                    axis_height = bbox.height

                    # Dynamically calculate font size based on plot area and text length
                    font_size = min(axis_width / 10, axis_height / 20)
                    axis.text(x, y, line_text, fontsize=font_size, color='blue', ha='center', va='center', weight='bold')
        else:
            line3, = ax[0].plot(dataGT[key][:, 0], dataGT[key][:, 1], linewidth=3, color='blue', label='Ground Truth')
            lines.append(line3)
            ax[1].plot(dataGT[key][:, 0], dataGT[key][:, 1], linewidth=3, color='blue')


        # perform metrics
        if ('Saccade' in key):
            try:
                rmse_l = saccade_metric('L', key, dataGaze, dataGT)
                rmse_r = saccade_metric('R', key, dataGaze, dataGT)
            except Exception as e:
                print(f"Error computing metric: {e}")
                rmse_l = "Error"
                rmse_r = "Error"
            ax[0].set_title(f"Left eye\nRMSE={rmse_l}")
            ax[1].set_title(f"Right eye\nRMSE={rmse_r}")
        elif('Smooth' in key):
            try:
                rmse_l, corr_l = smooth_pursuit_metric('L', key, dataGaze, dataGT)
                rmse_r, corr_r = smooth_pursuit_metric('R', key, dataGaze, dataGT)
            except Exception as e:
                print(f"Error computing metric: {e}")
                rmse_l, corr_l = "Error","Error"
                rmse_r, corr_r = "Error","Error"
            ax[0].set_title(f"Left eye\nRMSE={rmse_l} CORR={corr_l}")
            ax[1].set_title(f"Right eye\nRMSE={rmse_r} CORR={corr_r}")
        else:
            ax[0].set_title(f"Left eye")
            ax[1].set_title(f"Right eye")
        
    if plotPCData is True:
        fig.legend(handles=[line1, line2, line3], loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=3)
    else:
        fig.legend(handles=lines, loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=2)
    if pathToSave is not None:
        plt.savefig(f"{pathToSave}/{key}.png", bbox_inches='tight', dpi=100)
    plt.close(fig)
 
def process_excel_file(file_path, file_path_gaze, output_folder, plotPCData = False):
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
    if plotPCData is True:
        dataPC = process_participant_data(file_path, sheets)
    else:
        dataPC = None
    dataGaze = process_gaze_data(file_path, sheets)
    dataGT = process_ground_truth_data(file_path_gaze, sheets)
 
    text = "Hello\nTest\nHi"
    for sheet in sheets:
        eye_data_to_image(dataPC, dataGaze, dataGT, sheet, sheet, output_folder, plotPCData, text)
 
    return enabled_buttons