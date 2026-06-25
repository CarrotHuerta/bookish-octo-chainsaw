import numpy as np


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

    def get_positional_readings(self):
        try:
            self._x = float(self._driver.find_element_by_id("x-range").text.split(" ")[0])
            self._y = float(self._driver.find_element_by_id("y-range").text.split(" ")[0])
            self._z = float(self._driver.find_element_by_id("z-range").text.split(" ")[0])
        except ValueError:
            pass
        return self._x, self._y, self._z

    def correction_to_clicks_mapping(self, correction, reserved=False):
        clicks = 0
        if abs(correction) > 50:
            clicks = 50
        elif abs(correction) > 20:
            clicks = 35
        elif abs(correction) > 8:
            clicks = 20
        elif abs(correction) > 3:
            clicks = 8 if reserved else 12
        elif abs(correction) > 1:
            clicks = 4 if reserved else 8
        elif abs(correction) > 0.2:
            clicks = 2 if reserved else 2
        elif abs(correction) > 0.0:
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
        x, y, z = self.get_positional_readings()
        if abs(y) > 0.0 or abs(z) > 0.0 or self._y_clicks != 0 or self._z_clicks != 0:
            ycks = self.correction_to_clicks_mapping(y)
            self._y_clicks = self.fix_clicks(ycks, self._y_clicks, self._y_left, self._y_right)
            zcks = self.correction_to_clicks_mapping(z)
            self._z_clicks = self.fix_clicks(zcks, self._z_clicks, self._z_down, self._z_up)
        else:
            xcks = self.correction_to_clicks_mapping(x, True)
            self._x_clicks = self.fix_clicks(xcks, self._x_clicks, self._x_forward, self._x_back)

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
