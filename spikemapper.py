# spikemapper.py  —  WRO 2026 Mosaic Masters
#
# Puertos:
#   F = Rueda Derecha
#   D = Rueda Izquierda  (COUNTERCLOCKWISE)
#   A = Motor Subir Bloque
#   B = Motor Garra Principal
#   C = Sensor Centro
#   E = Sensor Derecho
#
# Canal BLE 0 → ENVÍA  (dist_mm, heading_deg, r, g, b)
# Canal BLE 1 → RECIBE (speed, turn, motor_cmd, motor_val, turn_cmd)
#
# motor_cmd:
#   0        = nada
#   1        = motor extra (garra)
#   2        = motor extra (subir bloque)
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
        self.subir_bloque    = Motor(Port.A)
        self.garra_principal = Motor(Port.B)
        self.sensor_centro = ColorSensor(Port.C)
        self.sensor_der    = ColorSensor(Port.E)
        self.drive  = DriveBase(self.left, self.right, wheel_diameter=86, axle_track=120)

        self.motor_map = {
            1: self.garra_principal,
            2: self.subir_bloque,
        }

        self.COLOR_RGB = {
            Color.RED:    (220,  50,  50),
            Color.YELLOW: (220, 200,  50),
            Color.GREEN:  ( 50, 200,  50),
            Color.BLUE:   ( 50,  50, 220),
            Color.WHITE:  (220, 220, 220),
            Color.NONE:   ( 40,  40,  40),
        }

        for s in (self.sensor_centro, self.sensor_der):
            s.detectable_colors(
                [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE, Color.WHITE]
            )
        self.drive.settings(
            straight_speed=300,
            straight_acceleration=600,
            turn_rate=200,
            turn_acceleration=400,
        )
        self.drive.reset()
        self.hub.imu.reset_heading(0)
        self.hub.light.on(Color.GREEN)

    def imu_turn(self, degrees):
        """Giro preciso usando el IMU — ambas ruedas coordinadas vía DriveBase."""
        target = self.hub.imu.heading() + degrees
        prev_error = 0

        while True:
            error = target - self.hub.imu.heading()

            # Normalizar a [-180, 180]
            if error > 180:  error -= 360
            if error < -180: error += 360

            if abs(error) < 2:
                break

            # Control PD: P rápido lejos, D amortigua oscilación cerca del target
            d_err = error - prev_error
            turn_rate = max(-300, min(300, error * 3.0 + d_err * 1.5))
            self.drive.drive(0, turn_rate)
            prev_error = error
            wait(10)

        self.drive.brake()

    def broadcast_state(self):
        dist_mm = int(self.drive.distance())
        heading = int(self.hub.imu.heading()) % 360
        try:
            r, g, b = self.COLOR_RGB.get(self.sensor_centro.color(), (0, 0, 0))
        except Exception:
            r, g, b = 0, 0, 0
        self.hub.ble.broadcast((dist_mm, heading, r, g, b))

    def run(self):
        prev_motor_cmd = 0
        prev_turn_cmd  = 0
        no_cmd_ticks   = 0   # paquetes BLE consecutivos sin recibir

        while True:
            cmd = self.hub.ble.observe(1)

            if cmd is not None and len(cmd) >= 5:
                no_cmd_ticks = 0
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
                    # Manejo continuo — DriveBase coordina ambas ruedas
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
                # Tolerar hasta 3 paquetes perdidos (≈150 ms) antes de frenar.
                # Esto evita paradas bruscas durante la transición del publicador BLE.
                no_cmd_ticks += 1
                if no_cmd_ticks >= 3:
                    self.drive.brake()
                    for m in self.motor_map.values():
                        m.brake()
                    prev_motor_cmd = 0
                    prev_turn_cmd  = 0

            self.broadcast_state()
            wait(50)


robot = Robot()
robot.run()
