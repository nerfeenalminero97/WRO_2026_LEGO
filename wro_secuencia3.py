from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Color
from pybricks.robotics import DriveBase
from pybricks.tools import wait

hub    = PrimeHub()
mi     = Motor(Port.B, Direction.COUNTERCLOCKWISE)
md     = Motor(Port.A, Direction.CLOCKWISE)
sensor = ColorSensor(Port.F)
robot  = DriveBase(mi, md, wheel_diameter=88, axle_track=115)

sensor.detectable_colors([Color.BLACK, Color.WHITE, Color.RED,
                          Color.GREEN, Color.BLUE, Color.YELLOW])

VELOCIDAD = 150    # mm/s - baja esto si las curvas siguen siendo problema
KP        = 2.0   # sube si no corrige suficiente en curvas
SIGN      = 1     # si siempre se va al lado equivocado, pon -1
OBJETIVO  = 50    # punto medio negro/blanco - ajusta segun tus valores de sensor_test

while True:
    error = sensor.reflection() - OBJETIVO
    giro  = SIGN * KP * error
    robot.drive(VELOCIDAD, giro)

    if abs(error) < 5:
        hub.light.on(Color.GREEN)   # centrado en el borde
    elif error > 0:
        hub.light.on(Color.ORANGE)  # ve blanco, gira a buscar negro
    else:
        hub.light.on(Color.CYAN)    # ve negro, gira al otro lado

    wait(10)
