# ============================================================
# spike_drive_receiver.py
# Corre este script en el SPIKE Prime v5 con Pybricks.
#
# El hub observa el canal BLE 1 esperando (speed, turn_rate)
# enviado desde la PC, y mueve los motores con DriveBase.
#
# Puerto F = rueda DERECHA
# Puerto B = rueda IZQUIERDA
# ============================================================

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Color
from pybricks.robotics import DriveBase
from pybricks.tools import wait

# Observa el canal 1 (la PC transmite ahí)
hub = PrimeHub(observe_channels=[1])

# Rueda derecha = Puerto F (gira en dirección normal)
# Rueda izquierda = Puerto B (gira al revés para ir hacia adelante)
right_motor = Motor(Port.F)
left_motor  = Motor(Port.B, Direction.COUNTERCLOCKWISE)

# DriveBase: ajusta wheel_diameter y axle_track a tu robot (mm)
drive = DriveBase(left_motor, right_motor, wheel_diameter=56, axle_track=112)

hub.light.on(Color.BLUE)

while True:
    data = hub.ble.observe(1)

    if data is not None:
        # data = (speed_mm_s, turn_rate_deg_s)
        speed, turn_rate = data
        drive.drive(speed, turn_rate)
        hub.light.on(Color.GREEN)
    else:
        # Sin señal → frenar
        drive.stop()
        hub.light.on(Color.ORANGE)

    wait(50)