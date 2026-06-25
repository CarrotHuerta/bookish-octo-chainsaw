import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

from dragon_position_controller_discrete import DragonPositionController
from dragon_rotation_controller_discrete import DragonRotationController


class AutomatedDocker:
    def __init__(self):
        fname = str(Path(__file__).resolve().parents[1]) + "/session_data.json"
        session_data = json.load(open(fname, "r"))
        self._driver = self.load_existing_firefox_session(
            session_data['session_url'],
            session_data['session_id']
        )
        self.restart()
        self._dragon_rot_ctl = DragonRotationController(self._driver)
        self._dragon_pos_ctl = DragonPositionController(self._driver)

    def load_existing_firefox_session(self, session_url, session_id):
        # Patch a new execute
        org_command_execute = RemoteWebDriver.execute

        def new_command_execute(self, command, params=None):
            if command == "newSession":
                return {'success': 0, 'value': None, 'sessionId': session_id}
            else:
                return org_command_execute(self, command, params)
        RemoteWebDriver.execute = new_command_execute

        driver = webdriver.Remote(command_executor=session_url, desired_capabilities={})
        driver.session_id = session_id

        # Replace the patched function with original function
        RemoteWebDriver.execute = org_command_execute
        return driver

    def begin_docking_sequence(self):
        print("- Dragon SpaceX starting docking sequence...")
        rot_success = self._dragon_rot_ctl.fix_state()
        pos_success = self._dragon_pos_ctl.fix_state()
        print("- Dragon SpaceX docking sequence complete.")
        if rot_success and pos_success:
            print("- We've a successful docking.")
        else:
            print("- Docking failed. Better luck(or code) next time!!")

    def restart(self):
        self._driver.find_element_by_id("option-restart").click()
        time.sleep(5.0)


if __name__ == "__main__":
    bot = AutomatedDocker()
    bot.begin_docking_sequence()
