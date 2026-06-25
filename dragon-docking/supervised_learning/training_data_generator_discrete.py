"""
This module will be used to generate training data to train any
supervised learning models. The continuous state space is reduced to
discrete state space. Other models for training data generator
can be built using similar interface.
"""

from pathlib import Path

import numpy as np


# Rotational data
"""
Correction mappings:
-3 = correction < -5
-2 = -5 <= correction < -1
-1 = -1 <= correction <= -0.1
0 = -0.1 < correction < 0.1
1 = 0.1 <= correction <= 1
2 = 1 < correction <= 5
3 = 5 < correction

Rate mappings:
-3 = -8 clicks
-2 = -4 clicks
-1 = -1 clicks
0 = 0 clicks
1 = 1 clicks
2 = 4 clicks
3 = 8 clicks

Action:
6 bits = [roll_right, roll_left, pitch_down, pitch_up, yaw_right, yaw_left] [0-5 indexing]
"""


def get_rot_correction_zone(correction):
    if abs(correction) > 5:
        return np.sign(correction)*3
    elif abs(correction) > 1:
        return np.sign(correction)*2
    elif abs(correction) >= 0.1:
        return np.sign(correction)*1
    else:
        return 0


def get_rot_rate_zone(clicks):
    if abs(clicks) > 8:
        return np.sign(clicks)*3.5
    elif abs(clicks) == 8:
        return np.sign(clicks)*3
    elif abs(clicks) > 4:
        return np.sign(clicks)*2.5
    elif abs(clicks) == 4:
        return np.sign(clicks)*2
    elif abs(clicks) > 1:
        return np.sign(clicks)*1.5
    elif abs(clicks) == 1:
        return np.sign(clicks)*1
    else:
        return 0


def rot_training_data_file():
    return "data/rotation_data_discrete.csv"


def rot_features():
    return ["roll", "pitch", "yaw", "roll_clicks", "pitch_clicks", "yaw_clicks"]


def rot_target():
    return 'action'


def _generate_rot_training_data():
    data_file = str(Path(__file__).resolve().parents[0]) + "/" + rot_training_data_file()
    writer = open(data_file, 'w')
    writer.write("roll,pitch,yaw,roll_clicks,pitch_clicks,yaw_clicks,action\n")
    for roll in range(-3, 4):
        for pitch in range(-3, 4):
            for yaw in range(-3, 4):
                for roll_clicks in np.arange(-3.5, 4, 0.5):
                    for pitch_clicks in np.arange(-3.5, 4, 0.5):
                        for yaw_clicks in np.arange(-3.5, 4, 0.5):
                            action = 0
                            roll_corr = roll - roll_clicks
                            if roll_corr != 0:
                                action = action | (1 << (0 if roll_corr > 0 else 1))
                            pitch_corr = pitch - pitch_clicks
                            if pitch_corr != 0:
                                action = action | (1 << (2 if pitch_corr > 0 else 3))
                            yaw_corr = yaw - yaw_clicks
                            if yaw_corr != 0:
                                action = action | (1 << (4 if yaw_corr > 0 else 5))
                            log_vals = [roll, pitch, yaw, roll_clicks, pitch_clicks, yaw_clicks, action]
                            writer.write(",".join([str(x) for x in log_vals])+"\n")
    writer.close()
    print("Rotational training data generated.")
# Rotational data end


# Positional data
"""
Correction mappings:
-4 = correction < -25
-3 = -25 <= correction < -8
-2 = -8 <= correction < -2
-1 = -2 <= correction <= 0.1
0 = -0.1 < correction < 0.1
1 = 0.1 <= correction <= 2
2 = 2 < correction <= 8
3 = 8 < correction <= 25
4 = 25 < correction

Rate mappings:
-4 = -50 clicks
-3 = -20 clicks
-2 = -8 clicks
-1 = -2 clicks
0 = 0 clicks
1 = 2 clicks
2 = 8 clicks
3 = 20 clicks
4 = 50 clicks

Action:
6 bits = [x_forward, x_back, y_left, y_right, z_down, z_up] [0-5 indexing]
"""


def get_pos_correction_zone(correction):
    if abs(correction) > 25:
        return np.sign(correction)*4
    elif abs(correction) > 8:
        return np.sign(correction)*3
    elif abs(correction) > 1:
        return np.sign(correction)*2
    elif abs(correction) >= 0.1:
        return np.sign(correction)*1
    else:
        return 0


def get_pos_rate_zone(clicks):
    if abs(clicks) > 50:
        return np.sign(clicks)*4.5
    elif abs(clicks) == 50:
        return np.sign(clicks)*4
    elif abs(clicks) > 20:
        return np.sign(clicks)*3.5
    elif abs(clicks) == 20:
        return np.sign(clicks)*3
    elif abs(clicks) > 8:
        return np.sign(clicks)*2.5
    elif abs(clicks) == 8:
        return np.sign(clicks)*2
    elif abs(clicks) > 1:
        return np.sign(clicks)*1.5
    elif abs(clicks) == 1:
        return np.sign(clicks)*1
    else:
        return 0


def pos_training_data_file():
    return "data/position_data_discrete.csv"


def pos_features():
    return ["x", "y", "z", "x_clicks", "y_clicks", "z_clicks"]


def pos_target():
    return 'action'


def _generate_pos_training_data():
    data_file = str(Path(__file__).resolve().parents[0]) + "/" + pos_training_data_file()
    writer = open(data_file, 'w')
    writer.write("x,y,z,x_clicks,y_clicks,z_clicks,action\n")
    for x in range(-4, 5):
        for y in range(-4, 5):
            for z in range(-4, 5):
                for x_clicks in np.arange(-4.5, 5, 0.5):
                    for y_clicks in np.arange(-4.5, 5, 0.5):
                        for z_clicks in np.arange(-4.5, 5, 0.5):
                            action = 0
                            if y != 0 or z != 0 or y_clicks != 0 or z_clicks != 0:
                                y_corr = y - y_clicks
                                if y_corr != 0:
                                    action = action | (1 << (2 if y_corr > 0 else 3))
                                z_corr = z - z_clicks
                                if z_corr != 0:
                                    action = action | (1 << (4 if z_corr > 0 else 5))
                            else:
                                x_corr = x - x_clicks
                                if x_corr != 0:
                                    action = action | (1 << (0 if x_corr > 0 else 1))
                            log_vals = [x, y, z, x_clicks, y_clicks, z_clicks, action]
                            writer.write(",".join([str(x) for x in log_vals])+"\n")
    writer.close()
    print("Positional training data generated.")
# Positional data end


if __name__ == "__main__":
    _generate_rot_training_data()
    _generate_pos_training_data()
