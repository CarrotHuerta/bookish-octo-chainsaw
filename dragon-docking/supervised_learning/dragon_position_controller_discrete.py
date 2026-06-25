import pickle
from pathlib import Path

from decision_tree_model_discrete import pos_model_file
from training_data_generator_discrete import (
    get_pos_correction_zone,
    get_pos_rate_zone
)


class DragonPositionController:
    def __init__(self, driver):
        self._driver = driver
        self._x_back = self._driver.find_element_by_id("translate-backward-button")
        self._x_forward = self._driver.find_element_by_id("translate-forward-button")
        self._x_clicks = 0
        self._y_left = self._driver.find_element_by_id("translate-left-button")
        self._y_right = self._driver.find_element_by_id("translate-right-button")
        self._y_clicks = 0
        self._z_up = self._driver.find_element_by_id("translate-up-button")
        self._z_down = self._driver.find_element_by_id("translate-down-button")
        self._z_clicks = 0
        self._x = 10.0
        self._y = 10.0
        self._z = 10.0
        self._docking_status = "RUNNING"

        model_file = str(Path(__file__).resolve().parents[0]) + "/" + pos_model_file()
        self._model = pickle.load(open(model_file, 'rb'))

    def update_positional_readings(self):
        try:
            self._x = float(self._driver.find_element_by_id("x-range").text.split(" ")[0])
            self._y = float(self._driver.find_element_by_id("y-range").text.split(" ")[0])
            self._z = float(self._driver.find_element_by_id("z-range").text.split(" ")[0])
        except ValueError:
            pass

    def get_curr_features(self):
        self.update_positional_readings()
        features = [get_pos_correction_zone(corr) for corr in [self._x, self._y, self._z]]
        features.append(get_pos_rate_zone(self._x_clicks))
        features.append(get_pos_rate_zone(self._y_clicks))
        features.append(get_pos_rate_zone(self._z_clicks))
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
        # print("X", self._x, self._x_clicks, action & (1 << 0), action & (1 << 1))
        # print("Y", self._y, self._y_clicks, action & (1 << 2), action & (1 << 3))
        # print("Z", self._z, self._z_clicks, action & (1 << 4), action & (1 << 5))
        if action & (1 << 0):
            self._x_clicks = self.fix_clicks(True, self._x_clicks, self._x_forward, self._x_back)
        if action & (1 << 1):
            self._x_clicks = self.fix_clicks(False, self._x_clicks, self._x_forward, self._x_back)
        if action & (1 << 2):
            self._y_clicks = self.fix_clicks(True, self._y_clicks, self._y_left, self._y_right)
        if action & (1 << 3):
            self._y_clicks = self.fix_clicks(False, self._y_clicks, self._y_left, self._y_right)
        if action & (1 << 4):
            self._z_clicks = self.fix_clicks(True, self._z_clicks, self._z_down, self._z_up)
        if action & (1 << 5):
            self._z_clicks = self.fix_clicks(False, self._z_clicks, self._z_down, self._z_up)

    def update_status(self):
        failed = self._driver.find_element_by_id("fail").value_of_css_property('visibility')
        passed = self._driver.find_element_by_id("success").value_of_css_property('visibility')
        if failed == "visible":
            self._docking_status = "FAILED"
        if passed == "visible":
            self._docking_status = "PASSED"

    def fix_state(self):
        print("- Positional state fixing started...")
        while self._docking_status == "RUNNING":
            self.correction_iteration()
            self.update_status()
        print("- Positional state fixing of Dragon is {}.".format(self._docking_status))
        return self._docking_status == "PASSED"
