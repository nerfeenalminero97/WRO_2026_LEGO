# wro_secuencia3.py  —  WRO 2026 Mosaic Masters
#
# Secuencia exportada del Simulador WRO 2026 (ruta v3).
# Sistema de coordenadas: (0,0) = esquina inferior izquierda del campo
#   X aumenta hacia la derecha, Y aumenta hacia arriba.
#   Robot arranca en (187, 193) mirando hacia +X (heading IMU = 0°).
#
# Presionar botón IZQUIERDO para iniciar.
#
# Puertos:
#   F = Rueda Derecha
#   D = Rueda Izquierda  (COUNTERCLOCKWISE)
#   A = Motor Garra Principal
#   B = Sensor de Color
#   E = Garra trasera (baldosas)
#   C = Expandir garra trasera

import umath as math
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Color, Button
from pybricks.robotics import DriveBase
from pybricks.tools import wait

# ════════════════════════════════════════════════════════════════════════
#  POSICIONES DEL CAMPO  (X mm, Y mm)
# ════════════════════════════════════════════════════════════════════════
INICIO     = (187,  193)

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

# Obstáculos (centros, mm) y distancia de seguridad para el robot 230×210mm
OBSTACLES  = [(860, 400), (860, 1010), (1560, 400), (1560, 1010)]
OBS_RADIO  = 65    # radio físico del obstáculo (mm)
ROBOT_HALF = 115   # mitad del ancho del robot: 230/2 mm
SAFE_DIST  = OBS_RADIO + ROBOT_HALF + 20   # 200 mm — margen total

# ════════════════════════════════════════════════════════════════════════
#  WAYPOINTS — exportados del Simulador WRO 2026 (ruta v3)
# ════════════════════════════════════════════════════════════════════════
WP00 = (187,  193)
WP01 = (661,  193)
WP02 = (970,  193)
WP03 = (970,   67)
WP04 = (498,   67)
WP05 = (498,  204)
WP06 = (1240, 204)
WP07 = (1240,  73)
WP08 = (1384,  73)
WP09 = (1461,  73)
WP10 = (1461, 204)
WP11 = (1710, 204)
WP12 = (1781, 204)
WP13 = (1860, 204)
WP14 = (1860, 315)
WP15 = (1860, 193)
WP16 = (1980, 193)
WP17 = (1980, 101)
WP18 = (2257, 101)
WP19 = (2257, 303)
WP20 = (1978, 303)
WP21 = (1978, 689)
WP22 = (1431, 689)
WP23 = (1431, 822)
WP24 = (1236, 822)
WP25 = (1201, 822)
WP26 = (1201, 1023)
WP27 = (1201, 820)
WP28 = (1435, 820)
WP29 = (1435, 684)
WP30 = (1987, 684)
WP31 = (1987, 453)
WP32 = (2306, 453)
WP33 = (2306, 566)
WP34 = (1976, 566)
WP35 = (1976, 699)
WP36 = (1427, 699)
WP37 = (1427, 684)
WP38 = (1993, 684)
WP39 = (1993, 998)
WP40 = (2281, 998)
WP41 = (1997, 998)
WP42 = (1997, 191)
WP43 = (1879, 191)
WP44 = (1238, 191)
WP45 = (1238, 397)
WP46 = (1238, 182)
WP47 = (2012, 182)
WP48 = (2012, 770)
WP49 = (2257, 770)
WP50 = (2257, 646)
WP51 = (2000, 646)
WP52 = (2000, 101)
WP53 = (1596, 101)
WP54 = (674,  101)
WP55 = (176,  101)
WP56 = (176,  200)
WP57 = (496,  200)
WP58 = (596,  200)
WP59 = (596,  371)
WP60 = (596,  586)
WP61 = (747,  586)
WP62 = (592,  586)
WP63 = (592,  461)
WP64 = (309,  461)
WP65 = (590,  461)
WP66 = (590,  732)
WP67 = (1150, 732)
WP68 = (590,  732)
WP69 = (590,  590)
WP70 = (318,  590)
WP71 = (603,  590)
WP72 = (603,  740)
WP73 = (1150, 740)
WP74 = (601,  740)
WP75 = (601,  809)
WP76 = (285,  809)
WP77 = (618,  809)
WP78 = (618,  742)
WP79 = (1156, 742)
WP80 = (605,  742)
WP81 = (605,  811)
WP82 = (605,  1008)
WP83 = (303,  1008)
WP84 = (609,  1008)
WP85 = (609,  744)
WP86 = (1161, 744)
WP87 = (603,  744)
WP88 = (603,  592)
WP89 = (753,  592)
WP90 = (753,  734)
WP91 = (903,  734)
WP92 = (603,  734)
WP93 = (603,  131)
WP94 = (159,  131)

# Zonas definidas en el simulador
ZONA_PARKING           = (1843, 391)   # [1759,249 → 1927,534]
ZONA_DIANA_BLANCO      = (1210, 1020)  # [1060,938 → 1360,1103]
ZONA_DIANA_VERDE       = (1434, 702)   # [1377,554 → 1491,850]
ZONA_DIANA_AMARILLO    = (1212, 405)   # [1058,337 → 1367,474]
ZONA_DIANA_AZUL        = (868,  699)   # [792,584  → 944,815]
ZONA_MARCO_DE_MOSAICO  = (1207, 708)   # [1096,620 → 1319,796]

# ════════════════════════════════════════════════════════════════════════
#  GARRA — calibrar en el robot
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


def _pt_seg_dist(px, py, ax, ay, bx, by):
    """Distancia mínima del punto (px,py) al segmento (ax,ay)-(bx,by), en mm."""
    dx, dy = bx - ax, by - ay
    len2 = dx * dx + dy * dy
    if len2 == 0:
        return math.sqrt((px - ax) ** 2 + (py - ay) ** 2)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / len2))
    return math.sqrt((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2)


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
        # Aceleración reducida para evitar sobreimpulso
        self.drive.settings(straight_speed=250, straight_acceleration=150,
                            turn_rate=200,       turn_acceleration=150)

        self.sensor.detectable_colors(
            [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE, Color.WHITE]
        )
        self.drive.reset()
        self.hub.imu.reset_heading(0)

        # Posición actual rastreada (dead-reckoning)
        self.pos_x, self.pos_y = INICIO

        self.hub.light.on(Color.GREEN)

    # ── Navegación ────────────────────────────────────────────────────────────

    def goto(self, target, _depth=0):
        """
        Navega hasta target=(X,Y) esquivando obstáculos automáticamente.
        Si la línea recta pasa a menos de SAFE_DIST de un obstáculo,
        calcula un punto de desvío y lo visita primero.
        """
        tx, ty = target
        if _depth < 4:
            for obs in OBSTACLES:
                ox, oy = obs
                if _pt_seg_dist(ox, oy, self.pos_x, self.pos_y, tx, ty) < SAFE_DIST:
                    bp = self._bypass(self.pos_x, self.pos_y, tx, ty, ox, oy)
                    if bp:
                        self.goto(bp, _depth + 1)
                        self.goto(target, _depth + 1)
                        return
        # Camino libre — ir directo
        dx = tx - self.pos_x
        dy = ty - self.pos_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 10:
            return
        heading_target = math.degrees(math.atan2(-dy, dx))
        self._ir_a(heading_target, round(dist))
        self.pos_x, self.pos_y = tx, ty

    def _bypass(self, ax, ay, bx, by, ox, oy):
        """
        Calcula el punto de desvío alrededor del obstáculo (ox,oy)
        en el camino A→B. Elige el lado que minimiza la distancia total
        y que quede dentro de los límites del campo.
        """
        dx, dy = bx - ax, by - ay
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1:
            return None
        nx, ny = -dy / length, dx / length
        margin = SAFE_DIST + 30
        best, best_cost = None, 999999999
        for side in (1, -1):
            wpx = ox + nx * side * margin
            wpy = oy + ny * side * margin
            if 80 <= wpx <= 2420 and 80 <= wpy <= 1020:
                cost = (math.sqrt((wpx - ax) ** 2 + (wpy - ay) ** 2) +
                        math.sqrt((bx - wpx) ** 2 + (by - wpy) ** 2))
                if cost < best_cost:
                    best_cost = cost
                    best = (wpx, wpy)
        return best

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

        # ── Secuencia exportada del Simulador WRO 2026 (ruta v3) ──
        self.pos_x, self.pos_y = 187, 193

        self.goto((661,  193))   # P1  — 474mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((970,  193))   # P2  — 309mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((970,   67))   # P3  — 126mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((498,   67))   # P4  — 472mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((498,  204))   # P5  — 137mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1240, 204))   # P6  — 742mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1240,  73))   # P7  — 131mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1384,  73))   # P8  — 144mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1461,  73))   # P9  — 77mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1461, 204))   # P10 — 131mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1710, 204))   # P11 — 249mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1781, 204))   # P12 — 71mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1860, 204))   # P13 — 79mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1860, 315))   # P14 — 111mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1860, 193))   # P15 — 122mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1980, 193))   # P16 — 120mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1980, 101))   # P17 — 92mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2257, 101))   # P18 — 277mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2257, 303))   # P19 — 202mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1978, 303))   # P20 — 279mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1978, 689))   # P21 — 386mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1431, 689))   # P22 — 547mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1431, 822))   # P23 — 133mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1236, 822))   # P24 — 195mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1201, 822))   # P25 — 35mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1201, 1023))  # P26 — 201mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1201, 820))   # P27 — 203mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1435, 820))   # P28 — 234mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1435, 684))   # P29 — 136mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1987, 684))   # P30 — 552mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1987, 453))   # P31 — 231mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2306, 453))   # P32 — 319mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2306, 566))   # P33 — 113mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1976, 566))   # P34 — 330mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1976, 699))   # P35 — 133mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1427, 699))   # P36 — 549mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1427, 684))   # P37 — 15mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1993, 684))   # P38 — 566mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1993, 998))   # P39 — 314mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2281, 998))   # P40 — 288mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1997, 998))   # P41 — 284mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1997, 191))   # P42 — 807mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1879, 191))   # P43 — 118mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1238, 191))   # P44 — 641mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1238, 397))   # P45 — 206mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1238, 182))   # P46 — 215mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2012, 182))   # P47 — 774mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2012, 770))   # P48 — 588mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2257, 770))   # P49 — 245mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2257, 646))   # P50 — 124mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2000, 646))   # P51 — 257mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((2000, 101))   # P52 — 545mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1596, 101))   # P53 — 404mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((674,  101))   # P54 — 922mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((176,  101))   # P55 — 498mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((176,  200))   # P56 — 99mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((496,  200))   # P57 — 320mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((596,  200))   # P58 — 100mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((596,  371))   # P59 — 171mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((596,  586))   # P60 — 215mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((747,  586))   # P61 — 151mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((592,  586))   # P62 — 155mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((592,  461))   # P63 — 125mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((309,  461))   # P64 — 283mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((590,  461))   # P65 — 281mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((590,  732))   # P66 — 271mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1150, 732))   # P67 — 560mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((590,  732))   # P68 — 560mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((590,  590))   # P69 — 142mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((318,  590))   # P70 — 272mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((603,  590))   # P71 — 285mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((603,  740))   # P72 — 150mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1150, 740))   # P73 — 547mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((601,  740))   # P74 — 549mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((601,  809))   # P75 — 69mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((285,  809))   # P76 — 316mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((618,  809))   # P77 — 333mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((618,  742))   # P78 — 67mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1156, 742))   # P79 — 538mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((605,  742))   # P80 — 551mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((605,  811))   # P81 — 69mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((605,  1008))  # P82 — 197mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((303,  1008))  # P83 — 302mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((609,  1008))  # P84 — 306mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((609,  744))   # P85 — 264mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((1161, 744))   # P86 — 552mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((603,  744))   # P87 — 558mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((603,  592))   # P88 — 152mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((753,  592))   # P89 — 150mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((753,  734))   # P90 — 142mm / -90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((903,  734))   # P91 — 150mm / 0°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((603,  734))   # P92 — 300mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((603,  131))   # P93 — 603mm / 90°
        self.garra_frontal_agarrar()  # TODO: o _soltar()
        self.goto((159,  131))   # P94 — 444mm / 180°
        self.garra_frontal_agarrar()  # TODO: o _soltar()

        self.hub.light.on(Color.GREEN)
        self.hub.display.text("OK")


robot = Robot()
robot.run()
