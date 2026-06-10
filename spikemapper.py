# spikemapper.py  —  WRO 2026 Mosaic Masters
#
# Puertos:
#   F = Rueda Derecha
#   D = Rueda Izquierda  (COUNTERCLOCKWISE)
#   A = Motor Garra Principal
#   E = Motor Agarrar Bloques
#   C = Motor Expandir Garra
#   B = Sensor de Color
#
# Canal BLE 0 → ENVÍA  (dist_mm, heading_deg, r, g, b)
# Canal BLE 1 → RECIBE (speed, turn, motor_cmd, motor_val, turn_cmd)
#
# motor_cmd:
#   0        = nada
#   1,2,3    = motores extra (garra, agarrar, expandir)
#   4        = drive.straight(motor_val mm)  ← preciso, encoder-based
#
# turn_cmd: 0=nada, +N=girar N° derecha, -N=girar N° izquierda

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Color
from pybricks.robotics import DriveBase
from pybricks.tools import wait


class Robot:
    def __init__(self):
        self.hub   = PrimeHub(observe_channels=[1], broadcast_channel=0)
        self.right = Motor(Port.F)
        self.left  = Motor(Port.D, Direction.COUNTERCLOCKWISE)
        self.garra_principal = Motor(Port.A)
        self.agarrar_bloques = Motor(Port.E)
        self.expandir_garra  = Motor(Port.C)
        self.sensor = ColorSensor(Port.B)
        self.drive  = DriveBase(self.left, self.right, wheel_diameter=86, axle_track=120)

        self.motor_map = {
            1: self.garra_principal,
            2: self.agarrar_bloques,
            3: self.expandir_garra,
        }

        self.COLOR_RGB = {
            Color.RED:    (220,  50,  50),
            Color.YELLOW: (220, 200,  50),
            Color.GREEN:  ( 50, 200,  50),
            Color.BLUE:   ( 50,  50, 220),
            Color.WHITE:  (220, 220, 220),
            Color.NONE:   ( 40,  40,  40),
        }

        self.sensor.detectable_colors(
            [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE, Color.WHITE]
        )
        self.drive.reset()
        self.hub.imu.reset_heading(0)
        self.hub.light.on(Color.GREEN)

    def imu_turn(self, degrees):
        """Giro preciso usando el IMU — no depende de axle_track ni de patinaje de ruedas."""
        target = self.hub.imu.heading() + degrees

        while True:
            error = target - self.hub.imu.heading()

            # Normalizar a [-180, 180]
            if error > 180:  error -= 360
            if error < -180: error += 360

            if abs(error) < 2:
                break

            # Control proporcional: rápido lejos, lento cerca
            turn_rate = max(-300, min(300, error * 2.5))
            self.drive.drive(0, turn_rate)
            wait(10)

        self.drive.stop()

    def broadcast_state(self):
        dist_mm = int(self.drive.distance())
        heading = int(self.hub.imu.heading()) % 360
        try:
            r, g, b = self.COLOR_RGB.get(self.sensor.color(), (0, 0, 0))
        except Exception:
            r, g, b = 0, 0, 0
        self.hub.ble.broadcast((dist_mm, heading, r, g, b))

    def run(self):
        prev_motor_cmd = 0
        prev_turn_cmd  = 0

        while True:
            cmd = self.hub.ble.observe(1)

            if cmd is not None and len(cmd) >= 5:
                speed     = int(cmd[0])
                turn      = int(cmd[1])
                motor_cmd = int(cmd[2])
                motor_val = int(cmd[3])
                turn_cmd  = int(cmd[4])

                # turn_cmd: solo ejecuta en el flanco de subida (0 → N)
                if turn_cmd != 0 and prev_turn_cmd == 0:
                    self.hub.light.on(Color.YELLOW)
                    self.imu_turn(turn_cmd)
                    self.hub.light.on(Color.GREEN)

                # motor_cmd=4: solo ejecuta en el flanco de subida (!=4 → 4)
                elif motor_cmd == 4 and prev_motor_cmd != 4:
                    self.hub.light.on(Color.CYAN)
                    self.drive.straight(motor_val)
                    self.hub.light.on(Color.GREEN)

                elif motor_cmd != 4 and turn_cmd == 0:
                    # Manejo continuo normal
                    self.drive.drive(speed, turn)

                    if motor_cmd in self.motor_map:
                        m = self.motor_map[motor_cmd]
                        m.run(motor_val) if motor_val != 0 else m.brake()
                    else:
                        for m in self.motor_map.values():
                            m.brake()

                prev_motor_cmd = motor_cmd
                prev_turn_cmd  = turn_cmd

            else:
                self.drive.stop()
                for m in self.motor_map.values():
                    m.brake()
                prev_motor_cmd = 0
                prev_turn_cmd  = 0

            self.broadcast_state()
            wait(50)


robot = Robot()
robot.run()
