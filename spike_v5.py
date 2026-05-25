from pybricks.hubs import PrimeHub
from pybricks.robotics import DriveBase
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Color, Stop, Direction
from pybricks.tools import wait

class Robot:
    def __init__(self):
        self.hub = PrimeHub()

        # Drive motors
        self.motor_mf = Motor(Port.F)
        self.motor_mb = Motor(Port.B, positive_direction=Direction.COUNTERCLOCKWISE)

        # Auxiliary large motor (used by some routines)
        self.motor_gd = Motor(Port.C)
        # Lift/collector motor
        self.motor_lc = Motor(Port.D)

        # Color sensors
        self.color_sensor1 = ColorSensor(Port.E)
        self.color_sensor2 = ColorSensor(Port.A)

        # state helpers
        self.lista_colores = []
        self.dicc_colores = {}
        self.var = 0

        self.move_tank = DriveBase(
            self.motor_mf,
            self.motor_mb,
            wheel_diameter=86,
            axle_track=120
        )

robot = Robot()

# Utility functions expected by interfaz.py

def pila(robot):
    voltaje = robot.hub.battery.voltage()
    try:
        robot.hub.display.number(voltaje)
    except Exception:
        pass

    if voltaje > 8000:
        robot.hub.light.on(Color.GREEN)
    elif voltaje > 7000:
        robot.hub.light.on(Color.YELLOW)
    else:
        robot.hub.light.on(Color.RED)

    porcentaje = int((voltaje - 7000) / 13)
    print(f'{porcentaje}% de pila')
    print(f'Voltaje = {voltaje}')


def calibrar(robot):
    # Simple calibration: show current sensor reflections once
    c2 = robot.color_sensor2.reflection()
    c1 = robot.color_sensor1.reflection()
    print(f'Calibrar: sensor2 reflection={c2}, sensor1 reflection={c1}')
    # optional visual feedback
    robot.hub.light.on(Color.BLUE)
    wait(500)
    robot.hub.light.on(Color.WHITE)


def stop(robot):
    try:
        robot.motor_mb.stop()
        robot.motor_mf.stop()
        print('stop: motors stopped')
    except Exception as e:
        print('stop: exception', e)


def motor_pair_reset(robot):
    robot.motor_mf.reset_angle(0)
    robot.motor_mb.reset_angle(0)


def motor_pair_distancia(velocidad, velocidad2, distancia, robot):
    try:
        print(f'motor_pair_distancia: running angles {velocidad},{velocidad2} for {distancia}')
        robot.motor_mf.run_angle(velocidad, distancia, wait=False)
        robot.motor_mb.run_angle(velocidad2, distancia)
        stop(robot)
    except Exception as e:
        print('motor_pair_distancia: exception', e)


def motor_pair_run(velocidad, velocidad2, robot):
    try:
        print(f'motor_pair_run: run speeds {velocidad},{velocidad2}')
        robot.motor_mf.run(velocidad)
        robot.motor_mb.run(velocidad2)
    except Exception as e:
        print('motor_pair_run: exception', e)


def motor_pair_time(velocidad, velocidad2, tiempo, robot):
    robot.motor_mf.run_time(velocidad, tiempo, wait=False)
    robot.motor_mb.run_time(velocidad2, tiempo)


def motor_pair_until_stalled(velocidad, velocidad2, robot):
    robot.motor_mf.run_until_stalled(velocidad)
    robot.motor_mb.run_until_stalled(velocidad2, wait=False)


def motor_pair_target(velocidad, velocidad2, angulo, robot):
    motor_pair_reset(robot)
    robot.motor_mf.run_target(velocidad, angulo, wait=False)
    robot.motor_mb.run_target(velocidad2, angulo)


def giroscopio(angulo, velocidad, velocidad2, comparador, robot):
    if comparador == 1:
        while True:
            motor_pair_run(velocidad, velocidad2, robot)
            if robot.hub.imu.heading() >= angulo:
                break
        stop(robot)

    elif comparador == 2:
        while True:
            motor_pair_run(velocidad, velocidad2, robot)
            if robot.hub.imu.heading() <= angulo:
                break
        stop(robot)

    else:  # comparador == 3 exact
        while True:
            motor_pair_run(velocidad, velocidad2, robot)
            if abs(robot.hub.imu.heading()) == angulo:
                break
        stop(robot)


def limitar(valor, minimo, maximo):
    if valor < minimo:
        return minimo
    if valor > maximo:
        return maximo
    return valor


def SA(angulo, condicion, velocidad, robot):
    kp = 0.4

    if condicion:
        robot.var += 1
        robot.move_tank.stop()
        return

    actual = robot.hub.imu.heading()
    error = angulo - actual

    if error > 180:
        error -= 360
    elif error < -180:
        error += 360

    if abs(error) < 2:
        error = 0

    giro = error * kp
    giro = limitar(giro, -30, 30)
    robot.move_tank.drive(velocidad, giro)


def SA_posicion_relativa(angulo, posicion_relativa, velocidad, masomenos, robot):
    robot.motor_mf.reset_angle(0)

    while robot.var != 1:
        if masomenos == 1:
            condicion = robot.motor_mf.angle() >= posicion_relativa
        elif masomenos == 2:
            condicion = robot.motor_mf.angle() <= posicion_relativa
        else:
            condicion = False

        SA(angulo, condicion, velocidad, robot)
        wait(10)

    robot.var = 0
    stop(robot)
    wait(100)


def SA_color_negro(repeticiones, angulo, velocidad, sensores, robot):
    while robot.var != repeticiones:
        if sensores == 1:
            SA(angulo, robot.color_sensor1.color() == Color.BLACK or (robot.color_sensor1.reflection() < 30 and robot.color_sensor1.reflection() > 5), velocidad, robot)
        elif sensores == 2:
            SA(angulo, robot.color_sensor2.color() == Color.BLACK or (robot.color_sensor2.reflection() < 30 and robot.color_sensor2.reflection() > 5), velocidad, robot)
        elif sensores == 3:
            SA(angulo, (robot.color_sensor1.color() == Color.BLACK and robot.color_sensor2.color() == Color.BLACK) or ((robot.color_sensor1.reflection() < 30 and robot.color_sensor1.reflection() > 5) and (robot.color_sensor2.reflection() < 30 and robot.color_sensor2.reflection() > 5)), velocidad, robot)
    stop(robot)
    robot.var = 0


if __name__ == '__main__':
    # simple smoke test when running on the hub directly
    pila(robot)
    wait(2000)
