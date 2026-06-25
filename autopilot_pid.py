"""
FASE 3: Despliegue en Python - Código de Control PID en Tiempo Discreto
Misión: Acople Autónomo Dragon 2 a ISS
"""

import time
import math
import threading
import matplotlib.pyplot as plt
from collections import deque
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

class DiscretePID:
    def __init__(self, Kp, Ki, Kd, Ts, u_min, u_max, tau=0.05):
        """
        Controlador PID en tiempo discreto.
        Incluye integración trapezoidal, derivación con filtro pasa-bajas y Anti-windup.
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.Ts = Ts

        # Límites para el Anti-windup
        self.u_min = u_min
        self.u_max = u_max

        # Filtro pasa-bajas para la derivada (constante de tiempo tau)
        # s = (2/Ts) * (z-1)/(z+1) (Tustin)
        self.tau = tau

        # Memoria del controlador
        self.e_prev = 0.0
        self.integral = 0.0
        self.derivative = 0.0

    def compute(self, setpoint, measurement):
        """
        Calcula la acción de control u(k) para el instante actual.
        """
        error = setpoint - measurement

        # Término Proporcional
        P = self.Kp * error

        # Término Integral (Aproximación Trapezoidal)
        # I(k) = I(k-1) + Ki * Ts * (e(k) + e(k-1)) / 2
        integral_update = self.integral + self.Ki * self.Ts * 0.5 * (error + self.e_prev)

        # Término Derivativo (Filtro Pasa-bajas)
        # D(k) = (2*tau - Ts)/(2*tau + Ts) * D(k-1) + (2*Kd)/(2*tau + Ts) * (e(k) - e(k-1))
        D = ( (2 * self.tau - self.Ts) / (2 * self.tau + self.Ts) ) * self.derivative \
            + (2 * self.Kd / (2 * self.tau + self.Ts)) * (error - self.e_prev)

        self.derivative = D

        # Acción de control continua calculada
        u = P + integral_update + D

        # Anti-windup: Saturación y Clamp condicional
        # Solo actualizamos el integrador si no estamos saturados
        # o si la actualización del integrador ayuda a salir de la saturación
        if u > self.u_max:
            u = self.u_max
            if error < 0: # El error quiere reducir u, permitimos integrar
                self.integral = integral_update
        elif u < self.u_min:
            u = self.u_min
            if error > 0:
                self.integral = integral_update
        else:
            self.integral = integral_update

        self.e_prev = error
        return u

class DeltaSigmaModulator:
    def __init__(self, threshold, output_mag):
        """
        Modulador Delta-Sigma de primer orden.
        Transforma una señal continua u(t) en pulsos discretos (clics).
        """
        self.sigma = 0.0 # Integrador de error
        self.threshold = threshold
        self.output_mag = output_mag

    def modulate(self, u_continuous):
        """
        Actualiza el acumulador y retorna la acción discreta (-1, 0, o 1).
        -1: Clic negativo (ej. Trans Down, Yaw Left)
         0: No hacer nada
         1: Clic positivo (ej. Trans Up, Yaw Right)
        """
        # Sumamos la entrada continua al acumulador
        self.sigma += u_continuous

        # Evaluamos el cuantizador
        if self.sigma >= self.threshold:
            self.sigma -= self.output_mag # Restamos la energía entregada por el pulso
            return 1
        elif self.sigma <= -self.threshold:
            self.sigma += self.output_mag
            return -1
        else:
            return 0

# --- CONFIGURACIÓN DE NAVEGADOR Y ELEMENTOS ---
def setup_driver():
    options = webdriver.FirefoxOptions()
    # options.add_argument('--headless') # Opcional: Descomentar si no hay GUI disponible
    driver = webdriver.Firefox(options=options)
    driver.get("https://iss-sim.spacex.com/")

    # Esperar hasta que el botón "BEGIN" esté disponible (el juego cargó)
    wait = WebDriverWait(driver, 60)
    try:
        start_btn = wait.until(lambda d: d.find_element(By.ID, "begin-button"))
        start_btn.click()
        time.sleep(2) # Tiempo de transición en la UI
    except Exception as e:
        print("El botón Begin no se detectó o se omitió. Asumiendo que la simulación ya está corriendo.")

    return driver

def get_float_from_xpath(driver, xpath, remove_chars):
    try:
        text = driver.find_element(By.XPATH, xpath).text
        # Ejemplo: text = "1.2 m" o "3.4°", removemos los caracteres extra al final
        if len(text) > remove_chars:
            return float(text[:len(text)-remove_chars])
        return 0.0
    except:
        return 0.0

def read_sensors(driver):
    """
    Extrae los datos de la UI.
    Devuelve un diccionario con las posiciones actuales (displacements).
    No usamos las velocidades rate[] porque el PID calcula la derivada discretamente.
    """
    state = {}

    # Translación (X es Range, Y y Z son los crosshairs)
    # Rango (x)
    state['x'] = get_float_from_xpath(driver, '//*[@id="range"]/div[2]', 2) # quita ' m'
    # Y y Z crosshair
    state['y'] = get_float_from_xpath(driver, '//*[@id="y-error"]', 2) # quita ' m'
    state['z'] = get_float_from_xpath(driver, '//*[@id="z-error"]', 2) # quita ' m'

    # Rotación
    state['roll'] = get_float_from_xpath(driver, '//*[@id="roll"]/div[1]', 1) # quita '°'
    state['pitch'] = get_float_from_xpath(driver, '//*[@id="pitch"]/div[1]', 1) # quita '°'
    state['yaw'] = get_float_from_xpath(driver, '//*[@id="yaw"]/div[1]', 1) # quita '°'

    return state

import queue

# --- GRÁFICAS EN TIEMPO REAL ---
# Usar colas thread-safe para pasar datos del hilo de control al hilo principal de matplotlib
data_queue = queue.Queue()

def live_plot():
    """
    Se ejecuta en el HILO PRINCIPAL para evitar errores fatales de Matplotlib
    con backends de GUI no thread-safe.
    """
    plt.ion()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8,6))

    plot_data = {
        't': deque(maxlen=200),
        'err_x': deque(maxlen=200),
        'err_y': deque(maxlen=200),
        'err_z': deque(maxlen=200),
        'u_x': deque(maxlen=200)
    }

    while True:
        try:
            # Procesar todos los datos nuevos en la cola
            while not data_queue.empty():
                new_data = data_queue.get_nowait()
                if new_data == "STOP":
                    plt.ioff()
                    plt.show()
                    return

                plot_data['t'].append(new_data['t'])
                plot_data['err_x'].append(new_data['err_x'])
                plot_data['err_y'].append(new_data['err_y'])
                plot_data['err_z'].append(new_data['err_z'])
                plot_data['u_x'].append(new_data['u_x'])

            if len(plot_data['t']) > 0:
                ax1.clear()
                ax2.clear()

                t = list(plot_data['t'])

                # Gráfica de Errores
                ax1.plot(t, list(plot_data['err_x']), label='Error X (Range)')
                ax1.plot(t, list(plot_data['err_y']), label='Error Y')
                ax1.plot(t, list(plot_data['err_z']), label='Error Z')
                ax1.set_title("Errores de Translación")
                ax1.set_ylabel("Metros (m)")
                ax1.legend(loc="upper right")
                ax1.grid(True)

                # Gráfica de Acción de Control
                ax2.step(t, list(plot_data['u_x']), label='u_x discreto (clics)', color='orange')
                ax2.set_title("Acción de Control Discreta (Eje X)")
                ax2.set_xlabel("Tiempo (s)")
                ax2.set_ylabel("Pulsos")
                ax2.legend(loc="upper right")
                ax2.grid(True)

            plt.pause(0.5)
        except KeyboardInterrupt:
            print("Visualización interrumpida.")
            break

# --- LAZO DE CONTROL PRINCIPAL ---
def main_control_loop():
    driver = setup_driver()

    # Referencias de botones
    buttons = {
        'x_pos': driver.find_element(By.ID, "translate-forward-button"),
        'x_neg': driver.find_element(By.ID, "translate-backward-button"),
        'y_pos': driver.find_element(By.ID, "translate-left-button"), # Y positivo -> izquierda
        'y_neg': driver.find_element(By.ID, "translate-right-button"),
        'z_pos': driver.find_element(By.ID, "translate-down-button"), # Z positivo -> abajo
        'z_neg': driver.find_element(By.ID, "translate-up-button"),

        'roll_pos': driver.find_element(By.ID, "roll-right-button"),
        'roll_neg': driver.find_element(By.ID, "roll-left-button"),
        'pitch_pos': driver.find_element(By.ID, "pitch-up-button"),
        'pitch_neg': driver.find_element(By.ID, "pitch-down-button"),
        'yaw_pos': driver.find_element(By.ID, "yaw-right-button"),
        'yaw_neg': driver.find_element(By.ID, "yaw-left-button")
    }

    # Tiempo de Muestreo (Ts = 0.2s, un buen balance para simulación web sin saturar el driver)
    Ts = 0.2

    # Sintonía (Política 2+3: Aproximación segura, sobreimpulso nulo, bajo gasto ITAE)
    # Ganancias estimadas basadas en el modelo de planta 1/ms^2 y 1/Js^2
    pid_x = DiscretePID(Kp=0.08, Ki=0.001, Kd=0.5, Ts=Ts, u_min=-1.0, u_max=1.0)
    pid_y = DiscretePID(Kp=0.15, Ki=0.005, Kd=0.8, Ts=Ts, u_min=-1.0, u_max=1.0)
    pid_z = DiscretePID(Kp=0.15, Ki=0.005, Kd=0.8, Ts=Ts, u_min=-1.0, u_max=1.0)

    pid_roll = DiscretePID(Kp=0.5, Ki=0.01, Kd=2.0, Ts=Ts, u_min=-1.0, u_max=1.0)
    pid_pitch = DiscretePID(Kp=0.5, Ki=0.01, Kd=2.0, Ts=Ts, u_min=-1.0, u_max=1.0)
    pid_yaw = DiscretePID(Kp=0.5, Ki=0.01, Kd=2.0, Ts=Ts, u_min=-1.0, u_max=1.0)

    # Moduladores
    mod_x = DeltaSigmaModulator(threshold=0.5, output_mag=1.0)
    mod_y = DeltaSigmaModulator(threshold=0.5, output_mag=1.0)
    mod_z = DeltaSigmaModulator(threshold=0.5, output_mag=1.0)

    mod_roll = DeltaSigmaModulator(threshold=0.5, output_mag=1.0)
    mod_pitch = DeltaSigmaModulator(threshold=0.5, output_mag=1.0)
    mod_yaw = DeltaSigmaModulator(threshold=0.5, output_mag=1.0)

    # Setpoints (La meta de acople es llegar al origen 0 en todos los ejes, salvo X que decrece hacia 0)
    sp = {'x': 0.0, 'y': 0.0, 'z': 0.0, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}

    print("Iniciando Acople Autónomo con Control PID (6 DOF)...")
    start_time = time.time()
    next_call = start_time

    try:
        while True:
            # 1. Temporización Estricta
            next_call += Ts
            sleep_time = next_call - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

            # 2. Medición del Estado Actual (Planta)
            state = read_sensors(driver)

            # Si se interactúa manualmente en el navegador, el estado cambiará inesperadamente.
            # Nuestro lazo cerrado es intrínsecamente robusto frente al "Rechazo de Perturbaciones",
            # ya que el error e(k) cambiará de signo/magnitud y el controlador compensará automáticamente.

            # 3. Cálculo de las leyes de control continuo u_c(k)
            # Para el rango (x), el error es X_referencia (0) - X_actual. Como X_actual es positivo (>0) y queremos que disminuya.
            # Si X=50, setpoint=0 -> error = -50. Queremos velocidad hacia adelante (x_pos = forward).
            # Invertimos el signo en la planta de X para alinear convenciones.
            u_c_x = pid_x.compute(0.0, -state['x']) # -(-50) = 50 -> error positivo -> empuje adelante
            u_c_y = pid_y.compute(sp['y'], state['y'])
            u_c_z = pid_z.compute(sp['z'], state['z'])

            u_c_roll = pid_roll.compute(sp['roll'], state['roll'])
            u_c_pitch = pid_pitch.compute(sp['pitch'], state['pitch'])
            u_c_yaw = pid_yaw.compute(sp['yaw'], state['yaw'])

            # 4. Modulación Delta-Sigma: u_c(k) continuo -> u_d(k) discreto
            u_d_x = mod_x.modulate(u_c_x)
            u_d_y = mod_y.modulate(u_c_y)
            u_d_z = mod_z.modulate(u_c_z)

            u_d_roll = mod_roll.modulate(u_c_roll)
            u_d_pitch = mod_pitch.modulate(u_c_pitch)
            u_d_yaw = mod_yaw.modulate(u_c_yaw)

            # 5. Ejecución del Actuador (Clics físicos en el navegador)
            if u_d_x == 1: buttons['x_pos'].click()
            elif u_d_x == -1: buttons['x_neg'].click()

            if u_d_y == 1: buttons['y_pos'].click()
            elif u_d_y == -1: buttons['y_neg'].click()

            if u_d_z == 1: buttons['z_pos'].click()
            elif u_d_z == -1: buttons['z_neg'].click()

            if u_d_roll == 1: buttons['roll_pos'].click()
            elif u_d_roll == -1: buttons['roll_neg'].click()

            if u_d_pitch == 1: buttons['pitch_pos'].click()
            elif u_d_pitch == -1: buttons['pitch_neg'].click()

            if u_d_yaw == 1: buttons['yaw_pos'].click()
            elif u_d_yaw == -1: buttons['yaw_neg'].click()

            # 6. Actualización de Gráficas en Tiempo Real
            current_t = time.time() - start_time

            data_queue.put({
                't': current_t,
                'err_x': state['x'],
                'err_y': state['y'],
                'err_z': state['z'],
                'u_x': u_d_x
            })

            # Condición de éxito: Rango < 0.2m, alienado < 0.2m/deg
            if (state['x'] < 0.2 and abs(state['y']) < 0.2 and abs(state['z']) < 0.2 and
                abs(state['roll']) < 0.2 and abs(state['pitch']) < 0.2 and abs(state['yaw']) < 0.2):
                print("¡ACOPLE EXITOSO CON LA ISS!")
                data_queue.put("STOP")
                break

    except KeyboardInterrupt:
        print("Interrupción del usuario. Deteniendo PID.")
        data_queue.put("STOP")
    except Exception as e:
        print(f"Error en hilo de control: {e}")
        data_queue.put("STOP")
    finally:
        # driver.quit() # Comentar si deseas mantener la ventana abierta
        pass

if __name__ == "__main__":
    # Iniciar el lazo de control en el hilo de fondo
    control_thread = threading.Thread(target=main_control_loop)
    control_thread.daemon = True
    control_thread.start()

    # Iniciar la gráfica en el HILO PRINCIPAL
    live_plot()
