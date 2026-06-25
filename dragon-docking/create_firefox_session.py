import json

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

def dump_session_data(driver):
    session_data = {}
    # En Selenium 4, '_url' cambió de lugar a '_client_config.remote_server_addr'
    session_data['session_url'] = driver.command_executor._client_config.remote_server_addr
    session_data['session_id'] = driver.session_id
    
    # Se recomienda usar 'with open' para un manejo seguro de archivos
    with open("session_data.json", 'w') as f:
        json.dump(session_data, f)


def open_firefox_session():
    options = Options()
    
    # En versiones modernas de Selenium/Geckodriver, Marionette es el valor por defecto
    # y pasar la capability explícitamente lanza un InvalidArgumentException.
    # Por lo tanto, se ha eliminado options.set_capability('marionette', True)
    
    # Se ha eliminado options.add_argument("disable-infobars") porque es exclusivo de Chrome.
    # En Firefox provocaba que el navegador intentara abrirlo como si fuera una página web.
    
    # Nota: En Selenium 4 la forma correcta de usar el modo headless es con un argumento:
    # options.add_argument("--headless")
    
    # Inicializamos el driver pasando únicamente 'options'
    driver = webdriver.Firefox(options=options)
    
    return driver


if __name__ == "__main__":
    driver = open_firefox_session()
    driver.set_page_load_timeout(600)
    driver.get("https://iss-sim.spacex.com")
    dump_session_data(driver)
    
    print("Session data dumped.")
    print("")
    print("-- Type EXIT and press enter to exit gracefully --")
    
    while input("> ") != "EXIT":
        continue
        
    driver.quit()