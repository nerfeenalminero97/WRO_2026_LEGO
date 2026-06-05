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
#  WAYPOINTS — exportados del Simulador WRO 2026
# ════════════════════════════════════════════════════════════════════════
WP00 = (217, 236)
WP01 = (1062, 253)
WP02 = (1053, 105)
WP03 = (755, 109)
WP04 = (532, 114)
WP05 = (1300, 107)
WP06 = (1450, 210)
WP07 = (1590, 260)
WP08 = (1742, 384)
WP09 = (1746, 264)
WP10 = (1757, 97)
WP11 = (1433, 101)
WP12 = (180, 139)
WP13 = (174, 238)
WP14 = (1852, 260)
WP15 = (1864, 178)
WP16 = (2047, 182)
WP17 = (2255, 210)
WP18 = (2251, 305)
WP19 = (1993, 315)
WP20 = (2023, 547)
WP21 = (2015, 654)
WP22 = (1759, 669)
WP23 = (1669, 667)
WP24 = (1536, 680)
WP25 = (1463, 785)
WP26 = (1270, 1002)
WP27 = (1266, 845)
WP28 = (1875, 759)
WP29 = (2042, 775)
WP30 = (2036, 478)
WP31 = (2255, 485)
WP32 = (1939, 493)
WP33 = (1892, 596)
WP34 = (1884, 693)
WP35 = (1783, 704)
WP36 = (1708, 704)
WP37 = (1575, 729)
WP38 = (1577, 790)
WP39 = (1845, 815)
WP40 = (1849, 942)
WP41 = (1849, 1017)
WP42 = (2027, 995)
WP43 = (2094, 995)
WP44 = (2246, 995)
WP45 = (2248, 783)
WP46 = (2242, 599)
WP47 = (2242, 371)
WP48 = (2242, 245)
WP49 = (1292, 249)
WP50 = (1210, 247)
WP51 = (1210, 384)
WP52 = (1208, 255)
WP53 = (687, 251)
WP54 = (663, 352)
WP55 = (663, 459)
WP56 = (530, 457)
WP57 = (436, 455)
WP58 = (324, 466)
WP59 = (493, 451)
WP60 = (626, 453)
WP61 = (672, 466)
WP62 = (680, 644)
WP63 = (860, 644)
WP64 = (980, 644)
WP65 = (1101, 657)
WP66 = (1208, 674)
WP67 = (599, 637)
WP68 = (472, 624)
WP69 = (382, 624)
WP70 = (326, 622)
WP71 = (1268, 697)
WP72 = (1219, 742)
WP73 = (1201, 798)
WP74 = (968, 798)
WP75 = (498, 807)
WP76 = (365, 807)
WP77 = (1193, 738)
WP78 = (1167, 845)
WP79 = (1045, 850)
WP80 = (599, 841)
WP81 = (453, 860)
WP82 = (369, 998)
WP83 = (657, 704)
WP84 = (1208, 684)
WP85 = (850, 710)
WP86 = (813, 729)

# Zonas definidas en el simulador
ZONA_PARKING           = (1734, 384)
ZONA_DIANA_BLANCO      = (1207, 996)
ZONA_MARCO_DE_MOSAICO  = (1226, 688)
ZONA_DIANA_VERDE       = (1556, 707)
ZONA_DIANA_AZUL        = (1213, 396)
ZONA_DIANA_AMARILLO    = (849, 702)

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

        # ── Secuencia exportada del Simulador WRO 2026 ──
        self.pos_x, self.pos_y = 217, 236
        self.goto((1062, 253))   # WP1
        self.goto((1053, 105))   # WP2
        self.goto((755, 109))    # WP3
        self.goto((532, 114))    # P4
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1300, 107))   # WP5
        self.goto((1450, 210))   # WP6
        self.goto((1590, 260))   # WP7
        self.goto((1742, 384))   # P8
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1746, 264))   # WP9
        self.goto((1757, 97))    # WP10
        self.goto((1433, 101))   # WP11
        self.goto((180, 139))    # P12
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((174, 238))    # P13
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1852, 260))   # WP14
        self.goto((1864, 178))   # WP15
        self.goto((2047, 182))   # WP16
        self.goto((2255, 210))   # P17
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2251, 305))   # WP18
        self.goto((1993, 315))   # WP19
        self.goto((2023, 547))   # WP20
        self.goto((2015, 654))   # WP21
        self.goto((1759, 669))   # WP22
        self.goto((1669, 667))   # WP23
        self.goto((1536, 680))   # WP24
        self.goto((1463, 785))   # WP25
        self.goto((1270, 1002))  # P26
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1266, 845))   # WP27
        self.goto((1875, 759))   # WP28
        self.goto((2042, 775))   # WP29
        self.goto((2036, 478))   # WP30
        self.goto((2255, 485))   # P31
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1939, 493))   # WP32
        self.goto((1892, 596))   # WP33
        self.goto((1884, 693))   # WP34
        self.goto((1783, 704))   # WP35
        self.goto((1708, 704))   # WP36
        self.goto((1575, 729))   # P37
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1577, 790))   # WP38
        self.goto((1845, 815))   # WP39
        self.goto((1849, 942))   # WP40
        self.goto((1849, 1017))  # WP41
        self.goto((2027, 995))   # WP42
        self.goto((2094, 995))   # WP43
        self.goto((2246, 995))   # P44
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2248, 783))   # WP45
        self.goto((2242, 599))   # P46
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2242, 371))   # WP47
        self.goto((2242, 245))   # WP48
        self.goto((1292, 249))   # WP49
        self.goto((1210, 247))   # WP50
        self.goto((1210, 384))   # WP51
        self.goto((1208, 255))   # WP52
        self.goto((687, 251))    # WP53
        self.goto((663, 352))    # WP54
        self.goto((663, 459))    # WP55
        self.goto((530, 457))    # WP56
        self.goto((436, 455))    # WP57
        self.goto((324, 466))    # P58
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((493, 451))    # WP59
        self.goto((626, 453))    # WP60
        self.goto((672, 466))    # WP61
        self.goto((680, 644))    # WP62
        self.goto((860, 644))    # WP63
        self.goto((980, 644))    # WP64
        self.goto((1101, 657))   # WP65
        self.goto((1208, 674))   # WP66
        self.goto((599, 637))    # WP67
        self.goto((472, 624))    # WP68
        self.goto((382, 624))    # WP69
        self.goto((326, 622))    # WP70
        self.goto((1268, 697))   # WP71
        self.goto((1219, 742))   # WP72
        self.goto((1201, 798))   # WP73
        self.goto((968, 798))    # WP74
        self.goto((498, 807))    # WP75
        self.goto((365, 807))    # WP76
        self.goto((1193, 738))   # WP77
        self.goto((1167, 845))   # WP78
        self.goto((1045, 850))   # WP79
        self.goto((599, 841))    # WP80
        self.goto((453, 860))    # WP81
        self.goto((369, 998))    # WP82
        self.goto((657, 704))    # WP83
        self.goto((1208, 684))   # WP84
        self.goto((850, 710))    # WP85
        self.goto((813, 729))    # P86
        self.garra_frontal_agarrar()  # TODO: o _soltar()

        self.hub.light.on(Color.GREEN)
        self.hub.display.text("OK")


robot = Robot()
robot.run()
