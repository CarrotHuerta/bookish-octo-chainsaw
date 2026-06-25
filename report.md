# Proyecto Final 2026-1: Control I - Acople Autónomo Dragon 2

## FASE 1: Modelamiento Matemático y Físico

### 1. Ecuaciones Diferenciales (6 DOF)
Para el modelamiento de la cápsula Dragon 2, asumimos dinámica de cuerpo rígido con masa y tensores de inercia constantes. En órbita, asumimos gravedad compensada (microgravedad) y fricción nula ($c=0$). Se definen los 6 grados de libertad: Translacionales ($x, y, z$) y Rotacionales ($\phi, \theta, \psi$ para Roll, Pitch, Yaw).

**Translacionales:**
A partir de la Segunda Ley de Newton:
$$ \sum F = m \ddot{\mathbf{r}} $$
Desacopladas en cada eje inercial (suponiendo pequeñas desviaciones angulares):
$$ m \ddot{x} = F_x \implies \ddot{x}(t) = \frac{1}{m} u_x(t) $$
$$ m \ddot{y} = F_y \implies \ddot{y}(t) = \frac{1}{m} u_y(t) $$
$$ m \ddot{z} = F_z \implies \ddot{z}(t) = \frac{1}{m} u_z(t) $$

**Rotacionales:**
Las ecuaciones de Euler para cuerpo rígido:
$$ \mathbf{\tau} = I \dot{\mathbf{\omega}} + \mathbf{\omega} \times (I \mathbf{\omega}) $$
Asumiendo un diseño simétrico con productos de inercia nulos ($I = \text{diag}(I_{xx}, I_{yy}, I_{zz})$) y despreciando los efectos giroscópicos no lineales para velocidades angulares pequeñas (linealización en torno al equilibrio estático $\mathbf{\omega} \approx 0$):
$$ I_{xx} \ddot{\phi} = \tau_\phi \implies \ddot{\phi}(t) = \frac{1}{I_{xx}} u_\phi(t) $$
$$ I_{yy} \ddot{\theta} = \tau_\theta \implies \ddot{\theta}(t) = \frac{1}{I_{yy}} u_\theta(t) $$
$$ I_{zz} \ddot{\psi} = \tau_\psi \implies \ddot{\psi}(t) = \frac{1}{I_{zz}} u_\psi(t) $$

En resumen, la planta linealizada se modela como sistemas de **doble integrador** $\frac{1}{ms^2}$ o $\frac{1}{Js^2}$, típicamente marginalmente estables.

### 2. Estimación de Parámetros
Para la cápsula SpaceX Crew Dragon 2, se asumen los siguientes valores realistas:
*   **Masa ($m$):** $\approx 9,525 \text{ kg}$ (con carga útil y propelente, simplificamos a $9,500 \text{ kg}$).
*   **Radio ($r$) y Altura ($h$):** $r \approx 2 \text{ m}, h \approx 8.1 \text{ m}$.
*   **Momentos de Inercia:** Aproximando la cápsula a un cilindro/cono uniforme:
    *   $I_{xx}$ (Roll, eje longitudinal): $\approx \frac{1}{2} m r^2 \approx 19,000 \text{ kg} \cdot \text{m}^2$.
    *   $I_{yy}, I_{zz}$ (Pitch, Yaw): $\approx \frac{1}{12} m (3r^2 + h^2) \approx 60,000 \text{ kg} \cdot \text{m}^2$.
*   **Propulsores Draco:** Cada motor provee $\approx 400 \text{ N}$. Asumiendo pares/configuraciones, el actuador puede proveer fuerzas combinadas de $\approx 800 \text{ N}$ a $1600 \text{ N}$.

### 3. El Modulador (Actuador basado en clics)
El PID continuo calcula una acción de control $u(t) \in \mathbb{R}$. Sin embargo, el simulador web solo acepta comandos de activación discreta (On/Off) vía "clics".
Para transformar $u(t)$ en una tasa de "clics" (comandos de disparo), implementaremos un **Modulador Delta-Sigma ($\Delta\Sigma$) de primer orden** (o modulación por densidad de pulsos).
*   **Dinámica:**
    1. Se acumula el error entre la salida de control continua deseada $u(k)$ y la salida discreta efectiva de los propulsores $y_p(k)$.
    2. El integrador del modulador: $\sigma(k) = \sigma(k-1) + [u(k) - y_p(k)]$.
    3. Cuantizador: Si $\sigma(k) > \text{Umbral}$, se envía un pulso positivo (Clic de empuje positivo) y $y_p(k) = U_{max}$. Si $\sigma(k) < -\text{Umbral}$, se envía un pulso negativo (Clic de empuje negativo) y $y_p(k) = -U_{max}$. De lo contrario, $y_p(k) = 0$.
Esto asegura que el promedio de los impulsos discretos entregue exactamente la misma fuerza promedio integral requerida por la señal continua del PID, limitando la saturación de los actuadores y evitando inestabilidades.

### 4. Diseño de Simulink (Conceptual)
1. **Bloque Setpoint (Referencia):** Señal constante de 0 (para Pitch, Yaw, Roll, y, z) y 0 para $x$ (con un acercamiento paulatino si es necesario).
2. **Bloque Comparador:** Calcula el Error: $e(t) = r(t) - y(t)$.
3. **Bloque PID:** Recibe $e(t)$ y computa la acción continua $u_c(t)$ usando bloques `Proporcional`, `Integrador`, y `Derivativo` (con filtro paso-bajo).
4. **Bloque Modulador (Relé / Histeresis / PWM):** Traduce $u_c(t)$ a $u_d(t) \in \{-1, 0, 1\} \times U_{max}$.
5. **Bloque Planta (Función de Transferencia):** $1 / (ms^2)$. Dos integradores en serie. El primero produce velocidad ($v$), el segundo posición ($p$).
6. **Realimentación:** La salida ($p$) regresa al comparador con signo negativo.
7. **Scopes:** Monitorean Setpoint vs Planta, señal PID continua vs salida del modulador, y el bloque de ITAE.

## FASE 2: Diseño del Sistema de Control PID

### 1. Funciones de Transferencia
Para el lazo cerrado, la planta es $G_p(s) = \frac{1}{ms^2}$ (traslación) o $G_p(s) = \frac{1}{Js^2}$ (rotación).
El controlador PID en forma paralela es:
$$ G_c(s) = K_p + \frac{K_i}{s} + K_d s = \frac{K_d s^2 + K_p s + K_i}{s} $$

**Lazo cerrado traslacional (ej. Eje Y):**
$$ T_y(s) = \frac{G_c(s) G_p(s)}{1 + G_c(s) G_p(s)} = \frac{\frac{K_d s^2 + K_p s + K_i}{m s^3}}{1 + \frac{K_d s^2 + K_p s + K_i}{m s^3}} $$
$$ T_y(s) = \frac{K_d s^2 + K_p s + K_i}{m s^3 + K_d s^2 + K_p s + K_i} $$

**Lazo cerrado rotacional (ej. Eje Pitch $\theta$):**
$$ T_\theta(s) = \frac{K_d s^2 + K_p s + K_i}{I_{yy} s^3 + K_d s^2 + K_p s + K_i} $$

La ecuación característica es de tercer orden ($s^3 + \frac{K_d}{M} s^2 + \frac{K_p}{M} s + \frac{K_i}{M} = 0$).

### 2. Filosofía de Sintonización (3 Políticas)
1. **Política 1: Tiempo de establecimiento rápido (Emergencias):**
   *   **Objetivo:** Minimizar $t_s$.
   *   **Estrategia:** Aumentar agresivamente $K_p$ para respuesta rápida y $K_d$ para añadir amortiguamiento crítico. Puede admitir sobreimpulso si se necesita esquivar un obstáculo, pero gasta demasiada energía (alto esfuerzo de control).
2. **Política 2: Sobreimpulso Nulo (Acople Crítico):**
   *   **Objetivo:** $\zeta \ge 1$ (Amortiguamiento crítico o sobreamortiguado). La cápsula no puede "pasarse" del target y colisionar con la ISS.
   *   **Estrategia:** Mantener $K_p$ moderado, $K_d$ alto para amortiguamiento fuerte, y $K_i$ bajo para evitar windup y oscilaciones. Es la política de seguridad estándar para maniobras de aproximación final.
3. **Política 3: Ahorro de Energía (Combustible mínimo):**
   *   **Objetivo:** Minimizar la variación de la acción de control $u(t)$ limitando los encendidos de los Draco.
   *   **Estrategia:** Valores muy bajos de $K_p, K_i, K_d$. Permitir una aproximación extremadamente lenta y asintótica, actuando sólo cuando el error excede umbrales considerables (incorporando bandas muertas).

**Elección Óptima para Acople:** Una combinación híbrida de Política 2 (para evitar colisión) y Política 3 (para cumplir el criterio ITAE de menor energía). Un sistema críticamente amortiguado con ganancias pequeñas para un acercamiento lento.

### 3. Criterio ITAE (Integral of Time-weighted Absolute Error)
El criterio ITAE penaliza fuertemente los errores que persisten en el tiempo:
$$ \text{ITAE} = \int_{0}^{\infty} t |e(t)| dt $$
Minimizar el ITAE produce respuestas con un sobreimpulso relativamente bajo y oscilaciones atenuadas, llevando al sistema al reposo.
Dado que la "energía" consumida por la nave es proporcional a la integral del valor absoluto del empuje $\int |u(t)| dt$, una sintonización basada en ITAE asegura que la trayectoria converge sin "chattering" (conmutación excesiva del actuador), optimizando el combustible. Un $e(t)$ que decae suavemente requiere intervenciones mínimas de los propulsores (menor "área" de la curva de control $u(t)$).

## FASE 4: Estructura del Informe de Ingeniería (IEEE Transactions)

El informe debe redactarse utilizando la plantilla oficial de la IEEE Transactions en LaTeX. A continuación, un esqueleto detallado para las 6 páginas:

```latex
\documentclass[journal]{IEEEtran}
\usepackage{amsmath, amssymb, graphicx}
\usepackage[utf8]{inputenc}
\usepackage{hyperref}

\begin{document}

\title{Control Discreto y Modelamiento para el Acople Autónomo de la Cápsula Dragon 2}
\author{Ingeniería de Control Espacial, Agencia Espacial Global}
\maketitle

\begin{abstract}
Este documento detalla el diseño e implementación de un sistema de control PID en tiempo discreto para gobernar los 6 grados de libertad de la cápsula Dragon 2 durante el acople con la ISS. Se aborda la obtención del modelo matemático, diseño de un modulador Delta-Sigma para actuadores On/Off (clics), sintonización híbrida basada en ITAE, y validación simulada con inyección de perturbaciones en tiempo real.
\end{abstract}

\section{Introducción}
\begin{itemize}
    \item Contexto de la exploración espacial y la relevancia del acople autónomo.
    \item Descripción breve de la cápsula Dragon 2 y sus actuadores Draco.
    \item Objetivos del control: Acercamiento suave, sobreimpulso nulo, minimización de energía.
\end{itemize}

\section{Modelamiento Matemático y Físico}
\subsection{Ecuaciones Diferenciales (6 DOF)}
\begin{itemize}
    \item Planteamiento de Newton-Euler para cuerpo rígido en microgravedad.
    \item $m \ddot{x} = u_x(t)$, $I_{xx} \ddot{\phi} = u_\phi(t)$, etc.
\end{itemize}
\subsection{Estimación de Parámetros}
\begin{itemize}
    \item Valores de masa $m \approx 9500$ kg y momentos de inercia ($I_{xx}, I_{yy}, I_{zz}$).
\end{itemize}
\subsection{Modulador Delta-Sigma}
\begin{itemize}
    \item Explicación de la conversión de la señal continua del PID a comandos discretos (clics).
    \item Ecuaciones del modulador: $\sigma(k) = \sigma(k-1) + [u(k) - y_p(k)]$.
\end{itemize}

\section{Diseño del Controlador PID}
\subsection{Lazo Cerrado y Funciones de Transferencia}
\begin{itemize}
    \item Ecuación característica: $s^3 + \frac{K_d}{M} s^2 + \frac{K_p}{M} s + \frac{K_i}{M} = 0$.
\end{itemize}
\subsection{Políticas de Sintonización}
\begin{itemize}
    \item Discusión de las 3 políticas: Rapidez, Seguridad ($\zeta \ge 1$), Eficiencia.
    \item Justificación de la elección híbrida.
\end{itemize}
\subsection{Optimización ITAE}
\begin{itemize}
    \item Uso del índice ITAE: $\int t |e(t)| dt$ para garantizar menor consumo de energía.
\end{itemize}

\section{Simulación y Validación}
\subsection{Configuración del Entorno (Python y Selenium)}
\begin{itemize}
    \item Descripción del loop de control con tiempo de muestreo estricto ($T_s$).
\end{itemize}
\subsection{Rechazo de Perturbaciones}
\begin{itemize}
    \item Resultados inyectando errores manuales en la interfaz.
\end{itemize}
\subsection{Gráficos de Desempeño}
\begin{itemize}
    \item Gráficas de error $x, y, z$ vs tiempo y acción de control (clics) vs tiempo.
\end{itemize}

\section{Conclusiones}
\begin{itemize}
    \item El modulador $\Delta\Sigma$ es vital para interfaces On/Off.
    \item La sintonización basada en ITAE garantiza el cumplimiento de la política de ahorro de combustible.
\end{itemize}

\end{document}
```
