import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

from dragon_position_controller import DragonPositionController
from dragon_rotation_controller import DragonRotationController


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
        # Parchear un nuevo execute (ejecutar)
        org_command_execute = RemoteWebDriver.execute

        def new_command_execute(self, command, params=None):
            if command == "newSession":
                # Modificado al formato W3C para Selenium 4
                return {'value': {'sessionId': session_id, 'capabilities': {}}}
            else:
                return org_command_execute(self, command, params)
        RemoteWebDriver.execute = new_command_execute

        options = webdriver.FirefoxOptions()
        driver = webdriver.Remote(command_executor=session_url, options=options)
        driver.session_id = session_id

        # Reemplazar la función parcheada con la función original
        RemoteWebDriver.execute = org_command_execute
        return driver

    def begin_docking_sequence(self):
        print("- Dragon SpaceX iniciando secuencia de acoplamiento...")
        rot_success = self._dragon_rot_ctl.fix_state()
        pos_success = self._dragon_pos_ctl.fix_state()
        print("- Secuencia de acoplamiento de Dragon SpaceX completada.")
        if rot_success and pos_success:
            print("- ¡Tenemos un acoplamiento exitoso!")
        else:
            print("- El acoplamiento falló. ¡Mejor suerte (o código) la próxima vez!")

    def restart(self):
        # Actualizado a la sintaxis de Selenium 4 usando By.ID
        self._driver.find_element(By.ID, "option-restart").click()
        time.sleep(5.0)


if __name__ == "__main__":
    bot = AutomatedDocker()
    bot.begin_docking_sequence()