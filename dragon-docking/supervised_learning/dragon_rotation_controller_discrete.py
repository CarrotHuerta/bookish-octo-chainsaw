import pickle
from pathlib import Path

from decision_tree_model_discrete import rot_model_file
from training_data_generator_discrete import (
    get_rot_correction_zone,
    get_rot_rate_zone
)


class DragonRotationController:
    def __init__(self, driver):
        self._driver = driver
        self._roll_left = self._driver.find_element_by_id("roll-left-button")
        self._roll_right = self._driver.find_element_by_id("roll-right-button")
        self._roll_clicks = 0
        self._pitch_up = self._driver.find_element_by_id("pitch-up-button")
        self._pitch_down = self._driver.find_element_by_id("pitch-down-button")
        self._pitch_clicks = 0
        self._yaw_left = self._driver.find_element_by_id("yaw-left-button")
        self._yaw_right = self._driver.find_element_by_id("yaw-right-button")
        self._yaw_clicks = 0
        self._roll_correction = 10.0
        self._pitch_correction = 10.0
        self._yaw_correction = 10.0
        self._docking_status = "RUNNING"

        model_file = str(Path(__file__).resolve().parents[0]) + "/" + rot_model_file()
        self._model = pickle.load(open(model_file, 'rb'))

    def update_rotational_readings(self):
        try:
            self._roll_correction = float(self._driver.find_element_by_id("roll").text.split("\n")[0][:-1])
            self._pitch_correction = float(self._driver.find_element_by_id("pitch").text.split("\n")[0][:-1])
            self._yaw_correction = float(self._driver.find_element_by_id("yaw").text.split("\n")[0][:-1])
        except ValueError:
            pass

    def get_curr_features(self):
        self.update_rotational_readings()
        corrs = [self._roll_correction, self._pitch_correction, self._yaw_correction]
        features = [get_rot_correction_zone(corr) for corr in corrs]
        features.append(get_rot_rate_zone(self._roll_clicks))
        features.append(get_rot_rate_zone(self._pitch_clicks))
        features.append(get_rot_rate_zone(self._yaw_clicks))
        return features

    def fix_clicks(self, increase, current_clicks, pos_corr, neg_corr):
        if increase:
            pos_corr.click()
            current_clicks += 1
        else:
            neg_corr.click()
            current_clicks -= 1
        return current_clicks

    def correction_iteration(self):
        features = self.get_curr_features()
        [action] = self._model.predict([features])
        # print("Roll:", self._roll_correction, self._roll_clicks, action & (1 << 0), action & (1 << 1))
        # print("Pitch:", self._pitch_correction, self._pitch_clicks, action & (1 << 2), action & (1 << 3))
        # print("Yaw:", self._yaw_correction, self._yaw_clicks, action & (1 << 4), action & (1 << 5))
        if action & (1 << 0):
            self._roll_clicks = self.fix_clicks(True, self._roll_clicks, self._roll_right, self._roll_left)
        if action & (1 << 1):
            self._roll_clicks = self.fix_clicks(False, self._roll_clicks, self._roll_right, self._roll_left)
        if action & (1 << 2):
            self._pitch_clicks = self.fix_clicks(True, self._pitch_clicks, self._pitch_down, self._pitch_up)
        if action & (1 << 3):
            self._pitch_clicks = self.fix_clicks(False, self._pitch_clicks, self._pitch_down, self._pitch_up)
        if action & (1 << 4):
            self._yaw_clicks = self.fix_clicks(True, self._yaw_clicks, self._yaw_right, self._yaw_left)
        if action & (1 << 5):
            self._yaw_clicks = self.fix_clicks(False, self._yaw_clicks, self._yaw_right, self._yaw_left)

    def update_status(self):
        self.update_rotational_readings()
        readings = [self._roll_correction, self._pitch_correction, self._yaw_correction]
        readings_set = all([abs(reading) <= 0.1 for reading in readings])
        clicks_set = all([clicks == 0 for clicks in [self._roll_clicks, self._pitch_clicks, self._yaw_clicks]])
        if readings_set and clicks_set:
            self._docking_status = "PASSED"

    def fix_state(self):
        print("- Rotational state fixing started...")
        while self._docking_status == "RUNNING":
            self.correction_iteration()
            self.update_status()
        print("- Rotational state fixing of Dragon is {}.".format(self._docking_status))
        return self._docking_status == "PASSED"
