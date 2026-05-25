# Mock implementation of spike_v5 API for desktop testing
import time
from types import SimpleNamespace

class MockMotor:
    def __init__(self, name):
        self.name = name
        self._angle = 0
        self._running = False

    def run(self, speed):
        self._running = True
        print(f"{self.name}.run({speed})")

    def stop(self):
        self._running = False
        print(f"{self.name}.stop()")

    def run_angle(self, speed, angle, wait=True):
        print(f"{self.name}.run_angle(speed={speed}, angle={angle}, wait={wait})")
        # simulate angle change
        self._angle += angle
        if wait:
            time.sleep(0.01)

    def run_time(self, speed, ms, wait=True):
        print(f"{self.name}.run_time(speed={speed}, ms={ms}, wait={wait})")
        if wait:
            time.sleep(ms/1000.0)

    def run_until_stalled(self, speed, wait=True):
        print(f"{self.name}.run_until_stalled(speed={speed})")

    def run_target(self, speed, target, wait=True):
        print(f"{self.name}.run_target(speed={speed}, target={target}, wait={wait})")
        self._angle = target

    def reset_angle(self, angle=0):
        print(f"{self.name}.reset_angle({angle})")
        self._angle = angle

    def angle(self):
        return self._angle

    def dc(self, d):
        print(f"{self.name}.dc({d})")


class MockColorSensor:
    def __init__(self, port):
        self.port = port
    def color(self):
        return None
    def reflection(self):
        return 50


class MockIMU:
    def __init__(self):
        self._heading = 0
    def heading(self):
        return self._heading
    def reset_heading(self, h):
        print(f"IMU.reset_heading({h})")
        self._heading = h


class MockBattery:
    def voltage(self):
        return 7500


class MockHub:
    def __init__(self):
        self.imu = MockIMU()
        self.battery = MockBattery()
        self.light = SimpleNamespace(on=lambda c: print(f"hub.light.on({c})"))
        self.display = SimpleNamespace(number=lambda n: print(f"hub.display.number({n})"))


class Robot:
    def __init__(self):
        self.hub = MockHub()
        self.motor_mf = MockMotor('motor_mf')
        self.motor_mb = MockMotor('motor_mb')
        self.motor_gd = MockMotor('motor_gd')
        self.motor_lc = MockMotor('motor_lc')
        self.color_sensor1 = MockColorSensor('E')
        self.color_sensor2 = MockColorSensor('A')
        self.lista_colores = []
        self.dicc_colores = {}
        self.var = 0
        # minimal DriveBase-like API
        self.move_tank = SimpleNamespace(straight=lambda d: print(f"move_tank.straight({d})"), stop=lambda: print("move_tank.stop()"), drive=lambda v,g: print(f"move_tank.drive({v},{g})"))

robot = Robot()

# Reuse the same function signatures as spike_v5

def pila(robot):
    voltaje = robot.hub.battery.voltage()
    robot.hub.display.number(voltaje)
    if voltaje > 8000:
        robot.hub.light.on('GREEN')
    elif voltaje > 7000:
        robot.hub.light.on('YELLOW')
    else:
        robot.hub.light.on('RED')
    porcentaje = int((voltaje - 7000) / 13)
    print(f'{porcentaje}% de pila (mock)')


def calibrar(robot):
    print('calibrar (mock)')


def stop(robot):
    robot.motor_mf.stop()
    robot.motor_mb.stop()


def motor_pair_reset(robot):
    robot.motor_mf.reset_angle(0)
    robot.motor_mb.reset_angle(0)


def motor_pair_distancia(velocidad, velocidad2, distancia, robot):
    print(f'mock motor_pair_distancia {velocidad},{velocidad2} dist={distancia}')
    robot.motor_mf.run_angle(velocidad, distancia, wait=False)
    robot.motor_mb.run_angle(velocidad2, distancia)
    stop(robot)


def motor_pair_run(velocidad, velocidad2, robot):
    print(f'mock motor_pair_run {velocidad},{velocidad2}')
    robot.motor_mf.run(velocidad)
    robot.motor_mb.run(velocidad2)


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
    print(f'mock giroscopio angle={angulo} speeds={velocidad},{velocidad2} comp={comparador}')
    # simulate immediate heading change
    robot.hub.imu._heading = angulo


def limitar(valor, minimo, maximo):
    if valor < minimo: return minimo
    if valor > maximo: return maximo
    return valor


def SA(angulo, condicion, velocidad, robot):
    print(f'mock SA angle={angulo} condicion={condicion} velocidad={velocidad}')
    if condicion:
        robot.var += 1
        robot.move_tank.stop()
        return
    robot.move_tank.drive(velocidad, 0)


def SA_posicion_relativa(angulo, posicion_relativa, velocidad, masomenos, robot):
    print(f'mock SA_posicion_relativa angle={angulo} pos={posicion_relativa} vel={velocidad} dir={masomenos}')
    robot.motor_mf.reset_angle(0)
    robot.motor_mf._angle = posicion_relativa
    robot.var = 0


def SA_color_negro(repeticiones, angulo, velocidad, sensores, robot):
    print('mock SA_color_negro')


if __name__ == '__main__':
    pila(robot)
    time.sleep(0.5)
    print('mock ready')
