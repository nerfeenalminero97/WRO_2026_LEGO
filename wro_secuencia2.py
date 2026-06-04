# wro_secuencia2.py  —  WRO 2026 Mosaic Masters
#
# Secuencia con coordenadas REALES del campo y lógica de garra.
# Sistema de coordenadas: (0,0) = esquina inferior izquierda del campo
#   X aumenta hacia la derecha, Y aumenta hacia arriba.
#   Robot arranca en (205, 205) mirando hacia +X (heading IMU = 0°).
#
# Presionar botón IZQUIERDO para iniciar.
#
# Puertos:
#   F = Rueda Derecha
#   D = Rueda Izquierda  (COUNTERCLOCKWISE)
#   A = Motor Garra Principal
#   B = Sensor de Color

import math
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Color, Button
from pybricks.robotics import DriveBase
from pybricks.tools import wait

# ════════════════════════════════════════════════════════════════════════
#  POSICIONES DEL CAMPO  (X mm, Y mm)
# ════════════════════════════════════════════════════════════════════════
INICIO     = (205,  205)

# Herramientas — recoger en estas posiciones
LLANA      = (910,  100)
CUENCO     = (1200, 100)
PALETA     = (1600, 100)

# Zona de entrega de herramientas
SPONSORS   = (602,  100)

# Bloques de cemento — almacenamiento lado derecho
CEM_BLANCO = (2360, 200)
CEM_AZUL   = (2360, 460)
CEM_VERDE  = (2360, 720)
CEM_AMARI  = (2360, 960)

# Baldosas — pilas lado izquierdo
TILE_AMARI = (330,  460)
TILE_AZUL  = (330,  610)
TILE_VERDE = (330,  760)
TILE_BLANC = (330,  910)

# Obstáculos (centros, radio ≈65mm — las rutas actuales los evitan)
# OBS_1=(860, 400)  OBS_2=(860,1010)  OBS_3=(1560,400)  OBS_4=(1560,1010)

# ════════════════════════════════════════════════════════════════════════
#  GARRA — calibrar en el robot (mismos motores que spikemapper.py)
#
#  Puerto A = garra_principal  → recoge herramientas y cemento (frente)
#  Puerto E = agarrar_bloques  → mecanismo trasero para baldosas
#  Puerto C = expandir_garra   → expansión del mecanismo trasero
#  Puerto B = sensor de color
# ════════════════════════════════════════════════════════════════════════
VEL_GARRA = 300   # deg/s velocidad de todos los motores de garra

# Garra frontal (Puerto A) — herramientas y cemento
G_FRONTAL_AGARRAR = 0    # TODO: grados para cerrar (ej: +200)
G_FRONTAL_SOLTAR  = 0    # TODO: grados para abrir  (ej: -200)

# Garra trasera (Puerto E) — agarrar baldosas
G_TRASERA_AGARRAR = 0    # TODO: grados para agarrar baldosa
G_TRASERA_SOLTAR  = 0    # TODO: grados para soltar baldosa

# Expandir garra (Puerto C) — expansión del mecanismo de baldosas
G_EXPANDIR        = 0    # TODO: grados para expandir
G_CONTRAER        = 0    # TODO: grados para contraer

RETROCESO_MM = 120   # mm que retrocede tras soltar un objeto


# ════════════════════════════════════════════════════════════════════════
#  ROBOT
# ════════════════════════════════════════════════════════════════════════
class Robot:
    def __init__(self):
        self.hub             = PrimeHub()
        self.right           = Motor(Port.F)
        self.left            = Motor(Port.D, Direction.COUNTERCLOCKWISE)
        self.garra_principal = Motor(Port.A)   # garra frontal
        self.agarrar_bloques = Motor(Port.E)   # garra trasera baldosas
        self.expandir_garra  = Motor(Port.C)   # expansión garra trasera
        self.sensor          = ColorSensor(Port.B)
        self.drive           = DriveBase(self.left, self.right, wheel_diameter=86, axle_track=120)

        self.sensor.detectable_colors(
            [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE, Color.WHITE]
        )
        self.drive.reset()
        self.hub.imu.reset_heading(0)

        # Posición actual rastreada (dead-reckoning)
        self.pos_x, self.pos_y = INICIO

        self.hub.light.on(Color.GREEN)

    # ── Navegación ────────────────────────────────────────────────────────────

    def goto(self, target):
        """
        Navega en línea recta desde la posición actual hasta target=(X,Y).
        Calcula el heading y la distancia automáticamente.
        """
        tx, ty = target
        dx = tx - self.pos_x
        dy = ty - self.pos_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 10:
            return
        heading_target = math.degrees(math.atan2(-dy, dx))
        self._ir_a(heading_target, round(dist))
        self.pos_x, self.pos_y = tx, ty

    def _ir_a(self, heading_abs, dist_mm):
        """Gira al heading absoluto y avanza dist_mm en línea recta."""
        turn = heading_abs - self.hub.imu.heading()
        if turn > 180:  turn -= 360
        if turn < -180: turn += 360
        self._imu_turn(turn)
        self.drive.straight(dist_mm)

    def _imu_turn(self, degrees):
        """Giro preciso con IMU."""
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

    def retroceder(self):
        """Retrocede RETROCESO_MM mm para liberar el objeto recién soltado."""
        self.drive.straight(-RETROCESO_MM)

    # ── Garra frontal — herramientas y cemento (Puerto A) ────────────────────

    def garra_frontal_agarrar(self):
        self.hub.light.on(Color.YELLOW)
        self.garra_principal.run_angle(VEL_GARRA, G_FRONTAL_AGARRAR)
        wait(400)
        self.hub.light.on(Color.GREEN)

    def garra_frontal_soltar(self):
        self.hub.light.on(Color.CYAN)
        self.garra_principal.run_angle(VEL_GARRA, G_FRONTAL_SOLTAR)
        wait(400)
        self.hub.light.on(Color.GREEN)

    # ── Garra trasera — baldosas (Puertos E + C) ──────────────────────────────

    def garra_trasera_agarrar(self):
        """Expande y cierra el mecanismo trasero para agarrar una baldosa."""
        self.hub.light.on(Color.YELLOW)
        self.expandir_garra.run_angle(VEL_GARRA, G_EXPANDIR)
        wait(200)
        self.agarrar_bloques.run_angle(VEL_GARRA, G_TRASERA_AGARRAR)
        wait(400)
        self.hub.light.on(Color.GREEN)

    def garra_trasera_soltar(self):
        """Suelta la baldosa y contrae el mecanismo trasero."""
        self.hub.light.on(Color.CYAN)
        self.agarrar_bloques.run_angle(VEL_GARRA, G_TRASERA_SOLTAR)
        wait(200)
        self.expandir_garra.run_angle(VEL_GARRA, G_CONTRAER)
        wait(400)
        self.hub.light.on(Color.GREEN)

    # ── Color sensor ──────────────────────────────────────────────────────────

    def leer_color(self):
        return self.sensor.color()

    # ── Misiones ──────────────────────────────────────────────────────────────

    def mision_herramientas(self):
        """
        Recoge las 3 herramientas y las lleva a Sponsors.
        """
        # Llana rectangular → Sponsors
        self.goto(LLANA)
        self.garra_frontal_agarrar()
        self.goto(SPONSORS)
        self.garra_frontal_soltar()
        self.retroceder()

        # Cuenco de cemento → Sponsors
        self.goto(CUENCO)
        self.garra_frontal_agarrar()
        self.goto(SPONSORS)
        self.garra_frontal_soltar()
        self.retroceder()

        # Paleta de albañilería → Sponsors
        self.goto(PALETA)
        self.garra_frontal_agarrar()
        self.goto(SPONSORS)
        self.garra_frontal_soltar()
        self.retroceder()

    def mision_cemento(self):
        """
        Recoge los bloques de cemento del almacenamiento (lado derecho).
        TODO: agregar las posiciones de entrega para cada color.
        """
        cemento = [
            (CEM_BLANCO, Color.WHITE),
            (CEM_AZUL,   Color.BLUE),
            (CEM_VERDE,  Color.GREEN),
            (CEM_AMARI,  Color.YELLOW),
        ]
        for pos, color in cemento:
            self.hub.light.on(color)
            self.goto(pos)
            self.garra_frontal_agarrar()
            # TODO: goto(ZONA_ENTREGA_COLOR) cuando se tengan las coordenadas
            self.garra_frontal_soltar()
            self.retroceder()

        self.hub.light.on(Color.GREEN)

    def mision_baldosas(self):
        """
        Recoge baldosas de las pilas del lado izquierdo.
        TODO: agregar goto al marco del mosaico para cada baldosa.
        """
        baldosas = [
            (TILE_AMARI, Color.YELLOW),
            (TILE_AZUL,  Color.BLUE),
            (TILE_VERDE, Color.GREEN),
            (TILE_BLANC, Color.WHITE),
        ]
        for pos, color in baldosas:
            self.hub.light.on(color)
            self.goto(pos)
            self.garra_trasera_agarrar()
            # TODO: goto(MARCO_MOSAICO) cuando se tenga el patrón y coordenadas
            self.garra_trasera_soltar()
            self.retroceder()

        self.hub.light.on(Color.GREEN)

    # ── Loop principal ────────────────────────────────────────────────────────

    def run(self):
        # Esperar botón izquierdo
        self.hub.display.text("GO?")
        while Button.LEFT not in self.hub.buttons.pressed():
            wait(50)
        self.hub.display.off()
        wait(300)

        self.hub.imu.reset_heading(0)
        self.drive.reset()

        self.mision_herramientas()
        self.mision_cemento()
        self.mision_baldosas()

        self.hub.light.on(Color.GREEN)
        self.hub.display.text("OK")


robot = Robot()
robot.run()
