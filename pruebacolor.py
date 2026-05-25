from pybricks.hubs import PrimeHub
from pybricks.robotics import DriveBase
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Color, Stop, Direction
from pybricks.tools import wait

from TrabajoDeShon import giroscopio

class Robot:
    def __init__(self):
        self.motor_mf = Motor(Port.A)
        self.motor_mb = Motor(Port.B, positive_direction=Direction.COUNTERCLOCKWISE)
        self.hub = PrimeHub()
        self.color_sensor = ColorSensor(Port.F)
        self.lista_colores = []
        self.dicc_colores = {}
        
        self.lista_colores = []
        self.color = 0
        self.dicc_colores = {}
        self.var = 0

        self.move_tank = DriveBase(
            self.motor_mf,
            self.motor_mb,
            wheel_diameter=86,
            axle_track=120
        )
        
robot = Robot()


def stop(robot):
    robot.motor_mb.stop()
    robot.motor_mf.stop()
    
def limitar(valor, minimo, maximo):
    if valor < minimo:
        return minimo
    if valor > maximo:
        return maximo
    return valor
    
def SA(angulo, condicion, velocidad, robot):
    kp = 0.4  # empieza bajo

    if condicion:
        robot.var += 1
        robot.move_tank.stop()
        return

    actual = robot.hub.imu.heading()

    error = angulo - actual

    # corregir salto entre 179 y -179
    if error > 180:
        error -= 360
    elif error < -180:
        error += 360

    # zona muerta: si el error es muy pequeño, no corrijas
    if abs(error) < 2:
        error = 0

    giro = error * kp

    # limitar giro para que no se vuelva loco
    giro = limitar(giro, -30, 30)

    robot.move_tank.drive(velocidad, giro)

def SA_posicion_relativa(angulo, posicion_relativa, velocidad, masomenos, robot):
    robot.motor_mf.reset_angle(0)

    while robot.var != 1:
        if masomenos == 1:
            condicion = robot.motor_mf.angle() >= posicion_relativa
        elif masomenos == 2:
            condicion = robot.motor_mf.angle() <= posicion_relativa

        SA(angulo, condicion, velocidad, robot)
        wait(10)

    robot.var = 0
    stop(robot)
    wait(100)

        
def leer_color(robot):
    giroscopio(90, -100, 100, 2, robot)
    for i in range(2):
        robot.color = robot.color_sensor.color()
        robot.lista_colores.append(robot.color)
        SA_posicion_relativa(-90, -75, -200, 2, robot)
        robot.color = 0 
    for i in range(2):
        robot.color = robot.color_sensor.color()
        robot.lista_colores.append(robot.color)
        SA_posicion_relativa(-90, 75, 200, 1, robot)
        robot.color = 0 
    giroscopio(175, -100, 100, 2, robot)
    SA_posicion_relativa(0, 200, 200, 1, robot)


def leer_lista(robot):
    for color in robot.lista_colores:
        if color in robot.dicc_colores:
            robot.dicc_colores[color] += 1
        else:
            robot.dicc_colores[color] = 1