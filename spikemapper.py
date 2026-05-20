# spike_wro.py  —  WRO 2026 Mosaic Masters
#
# Puertos:
#   F = Rueda Derecha
#   B = Rueda Izquierda  (COUNTERCLOCKWISE)
#   A = Motor Garra Principal
#   E = Motor Agarrar Bloques
#   C = Motor Expandir Garra
#   D = Sensor de Color
#
# Canal BLE 1 → recibe (speed, turn, motor_cmd, motor_val) desde la PC
# Canal BLE 0 → envía (color_code) a la PC
#
# motor_cmd:
#   0 = nada
#   1 = Garra Principal  (Puerto A)
#   2 = Agarrar Bloques  (Puerto E)
#   3 = Expandir Garra   (Puerto C)
# motor_val: velocidad en deg/s (positivo o negativo)

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Color
from pybricks.robotics import DriveBase
from pybricks.tools import wait

hub   = PrimeHub(observe_channels=[1], broadcast_channel=0)
right = Motor(Port.F)
left  = Motor(Port.B, Direction.COUNTERCLOCKWISE)
garra_principal = Motor(Port.A)
agarrar_bloques = Motor(Port.E)
expandir_garra  = Motor(Port.C)
sensor = ColorSensor(Port.D)

drive = DriveBase(left, right, wheel_diameter=56, axle_track=112)

MOTOR_MAP = {
    1: garra_principal,
    2: agarrar_bloques,
    3: expandir_garra,
}

COLOR_CODE = {
    Color.YELLOW: 1,
    Color.BLUE:   2,
    Color.GREEN:  3,
    Color.WHITE:  4,
    Color.RED:    5,
}

hub.light.on(Color.GREEN)

while True:
    cmd = hub.ble.observe(1)

    if cmd is not None and len(cmd) >= 4:
        speed      = int(cmd[0])
        turn       = int(cmd[1])
        motor_cmd  = int(cmd[2])
        motor_val  = int(cmd[3])

        # Mover ruedas
        drive.drive(speed, turn)

        # Mover motor extra si hay comando
        if motor_cmd != 0:
            m = MOTOR_MAP.get(motor_cmd)
            if m:
                if motor_val != 0:
                    m.run(motor_val)
                else:
                    m.stop()
        else:
            # Frenar todos los motores extra cuando no hay comando
            for m in MOTOR_MAP.values():
                m.stop()
    else:
        drive.stop()
        for m in MOTOR_MAP.values():
            m.stop()

    color_code = COLOR_CODE.get(sensor.color(), 0)
    hub.ble.broadcast((color_code,))

    wait(50)