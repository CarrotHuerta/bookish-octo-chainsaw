import numpy as np


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

    def get_rotational_readings(self):
        try:
            self._roll_correction = float(self._driver.find_element_by_id("roll").text.split("\n")[0][:-1])
            self._pitch_correction = float(self._driver.find_element_by_id("pitch").text.split("\n")[0][:-1])
            self._yaw_correction = float(self._driver.find_element_by_id("yaw").text.split("\n")[0][:-1])
        except ValueError:
            pass
        return self._roll_correction, self._pitch_correction, self._yaw_correction

    def correction_to_clicks_mapping(self, correction):
        clicks = 0
        if abs(correction) > 15:
            clicks = 10
        elif abs(correction) > 5:
            clicks = 8
        elif abs(correction) > 1.0:
            clicks = 5
        elif abs(correction) > 0.1:
            clicks = 1
        return np.sign(correction)*clicks

    def fix_clicks(self, expected_clicks, current_clicks, pos_corr, neg_corr):
        if expected_clicks == current_clicks:
            return current_clicks
        elif expected_clicks > current_clicks:
            pos_corr.click()
            current_clicks += 1
        elif expected_clicks < current_clicks:
            neg_corr.click()
            current_clicks -= 1
        return current_clicks

    def correction_iteration(self):
        roll, pitch, yaw = self.get_rotational_readings()
        rcks = self.correction_to_clicks_mapping(roll)
        self._roll_clicks = self.fix_clicks(rcks, self._roll_clicks, self._roll_right, self._roll_left)
        pcks = self.correction_to_clicks_mapping(pitch)
        self._pitch_clicks = self.fix_clicks(pcks, self._pitch_clicks, self._pitch_down, self._pitch_up)
        ycks = self.correction_to_clicks_mapping(yaw)
        self._yaw_clicks = self.fix_clicks(ycks, self._yaw_clicks, self._yaw_right, self._yaw_left)

    def update_status(self):
        roll, pitch, yaw = self.get_rotational_readings()
        readings_set = all([abs(reading) <= 0.1 for reading in [roll, pitch, yaw]])
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
