"""
WRO 2026 - Utilidad de CALIBRACION (corre en el hub, lee la CONSOLA).
Conecta el hub, corre este programa y observa los numeros que imprime.
Cambia la variable MODO segun lo que quieras calibrar.

Pasa los numeros que saques aqui a wro_primitivas.py.
"""

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait

# --- pon aqui TUS valores actuales y puertos ---
PUERTO_IZQ   = Port.A
PUERTO_DER   = Port.B
PUERTO_COLOR = Port.C
WHEEL_DIA    = 56.0       # mm (valor actual; lo vas a corregir)
AXLE_TRACK   = 112.0      # mm (valor actual; lo vas a corregir)

hub = PrimeHub()
sensor = ColorSensor(PUERTO_COLOR)
motor_izq = Motor(PUERTO_IZQ, Direction.COUNTERCLOCKWISE)
motor_der = Motor(PUERTO_DER)
robot = DriveBase(motor_izq, motor_der, wheel_diameter=WHEEL_DIA, axle_track=AXLE_TRACK)

# ============================================================
# ELIGE QUE CALIBRAR:  "sensor" | "distancia" | "giro"
# ============================================================
MODO = "sensor"

if MODO == "sensor":
    # Mueve el sensor sobre cada superficie y LEE los numeros.
    #  - Reflexion: anota el valor sobre NEGRO y sobre BLANCO.
    #  - HSV: anota H, S, V sobre cada color (amarillo, azul, verde, blanco),
    #         a la MISMA altura a la que leeras el mosaico.
    print("Leyendo sensor. Mueve el sensor sobre cada superficie. Ctrl-C para parar.")
    while True:
        r = sensor.reflection()
        c = sensor.hsv()
        print("reflexion:", r, " | H:", c.h, " S:", c.s, " V:", c.v)
        wait(300)

elif MODO == "distancia":
    # Mide con regla cuanto avanza REALMENTE y ajusta WHEEL_DIA.
    robot.use_gyro(True)
    wait(2000)            # quieto: deja calibrar el IMU
    print("Avanzando 1000 mm comandados. Mide la distancia REAL con regla.")
    robot.straight(1000)
    print("Nuevo WHEEL_DIA = WHEEL_DIA_actual * (real_mm / 1000)")

elif MODO == "giro":
    # Con gyro los giros ya salen exactos; esto solo valida el modelo (AXLE_TRACK).
    robot.use_gyro(False)   # apagado a proposito para medir el modelo mecanico
    wait(500)
    print("Girando 360 comandados. Marca el inicio y mide los grados REALES.")
    robot.turn(360)
    print("Nuevo AXLE_TRACK = AXLE_TRACK_actual * (360 / grados_reales)")
