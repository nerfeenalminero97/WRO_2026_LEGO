# wro_secuencia1.py  —  WRO 2026 Mosaic Masters
#
# Secuencia de prueba con waypoints reales medidos con mapgui.
# Flashear al hub y presionar botón IZQUIERDO para iniciar.
#
# Waypoints (coordenadas del mapgui):
#   Inicio           X=139,  Y=905
#   Llana rect.      X=831,  Y=1045
#   Sponsors         X=619,  Y=1040
#   Cuenco cemento   X=1131, Y=1040
#   Paleta alb.      X=1466, Y=1040
#   Cemento Blanco   X=2076, Y=895
#   Cemento Azul     X=2077, Y=624
#   Cemento Verde    X=2077, Y=557
#
# Puertos:
#   F = Rueda Derecha
#   D = Rueda Izquierda  (COUNTERCLOCKWISE)
#   A = Motor Garra Principal
#   B = Sensor de Color

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Color, Button
from pybricks.robotics import DriveBase
from pybricks.tools import wait

# ════════════════════════════════════════════════════════════════════════
#  CONSTANTES — calculadas de coordenadas mapgui con atan2(ΔX, -ΔY)
# ════════════════════════════════════════════════════════════════════════

# ── Tramo 1: Inicio → Llana rectangular ──────────────────────────────
A_LLANA  = 101   # °  heading IMU para ir directo a la llana
D_LLANA  = 706   # mm distancia

# ── Tramo 2: Llana rectangular → Sponsors ────────────────────────────
A_SPON   = -89   # °  heading absoluto IMU
D_SPON   = 212   # mm

# ── Tramo 3: Sponsors → Cuenco de cemento ────────────────────────────
A_CUENCO = 90    # °
D_CUENCO = 512   # mm

# ── Tramo 4: Cuenco → Paleta albañilería ─────────────────────────────
A_PALETA = 90    # °
D_PALETA = 335   # mm

# ── Tramo 5: Paleta → Cemento Blanco ─────────────────────────────────
A_CEM_B  = 77    # °
D_CEM_B  = 627   # mm

# ── Tramo 6: Cemento Blanco → Cemento Azul ───────────────────────────
A_CEM_A  = 0     # °
D_CEM_A  = 271   # mm

# ── Tramo 7: Cemento Azul → Cemento Verde ────────────────────────────
A_CEM_V  = 0     # °
D_CEM_V  = 67    # mm

# ── Garra (calibrar en el robot) ─────────────────────────────────────
VEL_GARRA     = 300  # deg/s
ANGULO_AGARRAR = 0   # TODO: calibrar — ángulo motor A para cerrar garra
ANGULO_SOLTAR  = 0   # TODO: calibrar — ángulo motor A para abrir garra


# ════════════════════════════════════════════════════════════════════════
#  ROBOT
# ════════════════════════════════════════════════════════════════════════
class Robot:
    def __init__(self):
        self.hub   = PrimeHub()
        self.right = Motor(Port.F)
        self.left  = Motor(Port.D, Direction.COUNTERCLOCKWISE)
        self.garra = Motor(Port.A)
        self.drive = DriveBase(self.left, self.right, wheel_diameter=86, axle_track=120)
        self.drive.reset()
        self.hub.imu.reset_heading(0)
        self.hub.light.on(Color.GREEN)

    def ir_a(self, heading_abs, dist_mm):
        """Gira al heading absoluto y avanza dist_mm en línea recta."""
        turn = heading_abs - self.hub.imu.heading()
        # normalizar a [-180, 180]
        if turn > 180:  turn -= 360
        if turn < -180: turn += 360
        self._imu_turn(turn)
        self.drive.straight(dist_mm)

    def _imu_turn(self, degrees):
        """Giro preciso con IMU — independiente de patinaje de ruedas."""
        target = self.hub.imu.heading() + degrees
        while True:
            error = target - self.hub.imu.heading()
            if error > 180:  error -= 360
            if error < -180: error += 360
            if abs(error) < 2:
                break
            turn_rate = max(-300, min(300, error * 2.5))
            self.drive.drive(0, turn_rate)
            wait(10)
        self.drive.stop()

    def esperar(self, ms=500):
        self.drive.stop()
        wait(ms)

    def run(self):
        # Esperar botón izquierdo para iniciar
        self.hub.display.text("GO?")
        while Button.LEFT not in self.hub.buttons.pressed():
            wait(50)
        self.hub.display.off()
        wait(300)

        self.hub.imu.reset_heading(0)
        self.drive.reset()

        # ── 1. Ir a la llana rectangular ─────────────────────────────
        self.hub.light.on(Color.YELLOW)
        self.ir_a(A_LLANA, D_LLANA)
        self.esperar()
        # self.garra.run_angle(VEL_GARRA, ANGULO_AGARRAR)  # TODO: descomentar

        # ── 2. Llevar llana a Sponsors ────────────────────────────────
        self.hub.light.on(Color.CYAN)
        self.ir_a(A_SPON, D_SPON)
        self.esperar()
        # self.garra.run_angle(VEL_GARRA, ANGULO_SOLTAR)   # TODO: descomentar

        # ── 3. Ir al cuenco de cemento ────────────────────────────────
        self.hub.light.on(Color.YELLOW)
        self.ir_a(A_CUENCO, D_CUENCO)
        self.esperar()
        # self.garra.run_angle(VEL_GARRA, ANGULO_AGARRAR)  # TODO: descomentar

        # ── 4. Llevar cuenco a paleta albañilería ─────────────────────
        self.hub.light.on(Color.CYAN)
        self.ir_a(A_PALETA, D_PALETA)
        self.esperar()
        # self.garra.run_angle(VEL_GARRA, ANGULO_SOLTAR)   # TODO: descomentar

        # ── 5. Ir a Cemento Blanco ────────────────────────────────────
        self.hub.light.on(Color.WHITE)
        self.ir_a(A_CEM_B, D_CEM_B)
        self.esperar()

        # ── 6. Ir a Cemento Azul ──────────────────────────────────────
        self.hub.light.on(Color.BLUE)
        self.ir_a(A_CEM_A, D_CEM_A)
        self.esperar()

        # ── 7. Ir a Cemento Verde ─────────────────────────────────────
        self.hub.light.on(Color.GREEN)
        self.ir_a(A_CEM_V, D_CEM_V)
        self.esperar()

        # ── FIN ───────────────────────────────────────────────────────
        self.hub.light.on(Color.GREEN)
        self.hub.display.text("OK")


robot = Robot()
robot.run()
