# spike_wro.py  —  WRO 2026
#
# Canal 1 → recibe (speed, turn) desde la PC  → mueve ruedas
# Canal 0 → envía solo el COLOR detectado     → la PC calcula X,Y
#
# La PC trackea la posición por dead reckoning
# (integra los comandos que ella misma manda)
#
# Puertos: F=derecha  B=izquierda  C=sensor color

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Color
from pybricks.robotics import DriveBase
from pybricks.tools import wait

hub    = PrimeHub(observe_channels=[1], broadcast_channel=0)
right  = Motor(Port.A)
left   = Motor(Port.B, Direction.COUNTERCLOCKWISE)
sensor = ColorSensor(Port.F)
drive  = DriveBase(left, right, wheel_diameter=56, axle_track=112)

COLOR_CODE = {
    Color.YELLOW: 1,
    Color.BLUE:   2,
    Color.GREEN:  3,
    Color.WHITE:  4,
    Color.RED:    5,
}

hub.light.on(Color.GREEN)

while True:
    # Recibir comando de la PC
    cmd = hub.ble.observe(1)
    if cmd is not None:
        speed, turn = int(cmd[0]), int(cmd[1])
        drive.drive(speed, turn)
    else:
        drive.stop()

    # Leer color y enviarlo a la PC (solo el color, sin odometria)
    color_code = COLOR_CODE.get(sensor.color(), 0)
    hub.ble.broadcast((color_code,))

    wait(100)