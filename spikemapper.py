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
# Canal BLE 0 → ENVÍA  (dist_mm, heading_deg, color_hex_r, color_hex_g, color_hex_b)
# Canal BLE 1 → RECIBE (speed, turn, motor_cmd, motor_val, turn_cmd)
#
# turn_cmd: 0=nada, +N=girar N grados derecha, -N=girar N grados izquierda
#           El hub ejecuta drive.turn() localmente — preciso y sin delay BLE
#
# motor_cmd: 0=nada, 1=GarraPrincipal(A), 2=AgarrarBloques(E), 3=ExpandirGarra(C)

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Color, Stop
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
drive.settings(
    straight_speed=400,
    straight_acceleration=200,
    turn_rate=200,
    turn_acceleration=200,
)

MOTOR_MAP = {
    1: garra_principal,
    2: agarrar_bloques,
    3: expandir_garra,
}

# Reset al inicio
drive.reset()
hub.imu.reset_heading(0)
hub.light.on(Color.GREEN)

while True:
    cmd = hub.ble.observe(1)

    if cmd is not None and len(cmd) >= 5:
        speed     = int(cmd[0])
        turn      = int(cmd[1])
        motor_cmd = int(cmd[2])
        motor_val = int(cmd[3])
        turn_cmd  = int(cmd[4])

        # Giro preciso — el hub lo ejecuta localmente, bloqueante
        if turn_cmd != 0:
            hub.light.on(Color.YELLOW)
            drive.turn(turn_cmd)   # bloquea hasta terminar el giro
            hub.light.on(Color.GREEN)
        else:
            # Drive normal
            drive.drive(speed, turn)

            # Motores extra
            if motor_cmd != 0:
                m = MOTOR_MAP.get(motor_cmd)
                if m:
                    if motor_val != 0:
                        m.run(motor_val)
                    else:
                        m.brake()
            else:
                for m in MOTOR_MAP.values():
                    m.brake()
    else:
        drive.stop()
        for m in MOTOR_MAP.values():
            m.brake()

    # Leer estado
    dist_mm  = int(drive.distance())
    heading  = int(hub.imu.heading()) % 360   # normalizar a 0-359

    # Color como RGB (sensor.rgb() devuelve 0-100, convertir a 0-255)
    try:
        rgb = sensor.rgb()
        r = int(rgb[0] * 2.55)
        g = int(rgb[1] * 2.55)
        b = int(rgb[2] * 2.55)
    except Exception:
        r, g, b = 0, 0, 0

    hub.ble.broadcast((dist_mm, heading, r, g, b))

    wait(50)