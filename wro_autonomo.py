# wro_autonomo.py  —  WRO 2026 Mosaic Masters
#
# Programa de misión autónoma completa para el SPIKE Prime.
# Este archivo se flashea al hub para la competencia.
# Para pruebas y mapeo de distancias, seguir usando spikemapper.py + mapgui.py.
#
# ════════════════════════════════════════════════════════════════════════════
#  FLUJO DE COMPETENCIA
#  1. Abre mapgui.py en la computadora
#  2. Lee el papel bajo el marco del mosaico (patrón 4×3 de colores)
#  3. Haz click en cada celda del grid en el GUI para seleccionar su color
#  4. Presiona "Enviar Patron" → hub se pone NARANJA (patrón recibido)
#  5. Presiona "Iniciar Mision" → hub se pone CYAN y corre autónomo
#
#  ALTERNATIVA SIN GUI (fallback):
#    Edita MOSAIC_PATTERN_FALLBACK abajo, pon USE_FALLBACK = True,
#    flashea el hub y presiona el botón izquierdo para iniciar.
# ════════════════════════════════════════════════════════════════════════════
#
# Puertos:
#   F = Rueda Derecha
#   D = Rueda Izquierda  (COUNTERCLOCKWISE)
#   A = Motor Garra Principal
#   E = Motor Agarrar Bloques
#   C = Motor Expandir Garra
#   B = Sensor de Color

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Color, Button
from pybricks.robotics import DriveBase
from pybricks.tools import wait

# ════════════════════════════════════════════════════════════════════════════
#  FALLBACK — editar si no se usa el GUI
# ════════════════════════════════════════════════════════════════════════════
USE_FALLBACK = False   # Cambiar a True para usar el patrón hardcodeado

# Patrón de ejemplo (leer el papel del campo y escribir aquí si USE_FALLBACK=True)
# Orden: fila 0 izq→der, fila 1 izq→der, fila 2 izq→der, fila 3 izq→der
# Valores: "Y"=Amarillo  "B"=Azul  "G"=Verde  "W"=Blanco
MOSAIC_PATTERN_FALLBACK = [
    "Y", "B", "G",   # fila 0 (superior)
    "G", "W", "Y",   # fila 1
    "B", "W", "G",   # fila 2
    "Y", "B", "W",   # fila 3 (inferior)
]

# ════════════════════════════════════════════════════════════════════════════
#  CONSTANTES DE CAMPO — MEDIR CON EL MAPPER ANTES DE CADA COMPETENCIA
#
#  Cómo medir cada distancia:
#    1. Flashea spikemapper.py al hub y abre mapgui.py
#    2. Haz click en el mapa para colocar el origen del robot (zona de inicio)
#    3. Maneja con WASD hasta el punto objetivo
#    4. Lee el X e Y en el GUI (parte inferior del canvas)
#    5. Calcula el heading relativo (el GUI lo muestra en Hdg=)
#    6. Escribe los valores en las constantes de abajo
# ════════════════════════════════════════════════════════════════════════════

# ── Herramientas ──────────────────────────────────────────────────────────────
DIST_PALETA_RECT_MM   = 0    # TODO: medir — distancia desde inicio a paleta rectangular
ANGLE_PALETA_RECT     = 0    # TODO: medir — heading IMU al llegar a paleta rectangular

DIST_PATROCINADOR_MM  = 0    # TODO: medir — distancia del área de patrocinadores
ANGLE_PATROCINADOR    = 0    # TODO: medir

DIST_CUENCO_MM        = 0    # TODO: medir — distancia al cuenco de cemento
ANGLE_CUENCO          = 0    # TODO: medir

DIST_PARKING_MM       = 0    # TODO: medir — distancia al espacio de estacionamiento
ANGLE_PARKING         = 0    # TODO: medir

DIST_PALETA_ALB_MM    = 0    # TODO: medir — distancia a la paleta de albañilería
ANGLE_PALETA_ALB      = 0    # TODO: medir

# ── Cemento ───────────────────────────────────────────────────────────────────
# El almacenamiento está en el extremo derecho. Las zonas objetivo en el centro.
# Cada color tiene un offset diferente dentro del área de almacenamiento.
ANGLE_IR_DERECHA      = 90   # TODO: verificar — heading para ir al almacenamiento
DIST_CEMENTO_BASE_MM  = 0    # TODO: medir — distancia base al primer color del cemento

# Offsets horizontales de cada color en el almacenamiento (en mm desde la base)
CEMENTO_OFFSET = {
    Color.YELLOW: 0,    # TODO: medir
    Color.BLUE:   0,    # TODO: medir
    Color.GREEN:  0,    # TODO: medir
    Color.WHITE:  0,    # TODO: medir
}

DIST_ZONA_OBJ_MM      = 0    # TODO: medir — distancia a las zonas objetivo del cemento
# Offsets de las zonas objetivo por color
ZONA_OBJ_OFFSET = {
    Color.YELLOW: 0,    # TODO: medir
    Color.BLUE:   0,    # TODO: medir
    Color.GREEN:  0,    # TODO: medir
    Color.WHITE:  0,    # TODO: medir
}

# ── Mosaico ───────────────────────────────────────────────────────────────────
ANGLE_IR_IZQUIERDA    = -90  # TODO: verificar — heading para ir a las pilas de tiles
DIST_TILES_BASE_MM    = 0    # TODO: medir — distancia a la primera pila de tiles

# Offset de cada pila de tiles por color (izquierda del campo)
TILE_OFFSET = {
    Color.YELLOW: 0,    # TODO: medir
    Color.BLUE:   0,    # TODO: medir
    Color.GREEN:  0,    # TODO: medir
    Color.WHITE:  0,    # TODO: medir
}

DIST_MARCO_MM         = 0    # TODO: medir — distancia al borde del marco de mosaico
PASO_FILA_MM          = 60   # TODO: medir — separación entre filas del marco (mm)
PASO_COL_MM           = 60   # TODO: medir — separación entre columnas del marco (mm)

# ── Garra (ángulos del motor A en grados) ─────────────────────────────────────
ANGULO_RECOGER        = 0    # TODO: calibrar — ángulo del motor A para recoger
ANGULO_SOLTAR         = 0    # TODO: calibrar — ángulo del motor A para soltar
VEL_GARRA             = 300  # Velocidad del motor de garra (deg/s)


# ════════════════════════════════════════════════════════════════════════════
#  ROBOT
# ════════════════════════════════════════════════════════════════════════════
class Robot:
    STATE_MANUAL  = 0   # Esperando patrón vía BLE o botón
    STATE_READY   = 1   # Patrón cargado, esperando señal de inicio
    STATE_RUNNING = 2   # Ejecutando misión autónoma

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

        self._state          = self.STATE_MANUAL
        self._mosaic_pattern = []

        self.hub.light.on(Color.GREEN)

    # ════════════════════════════════════════════════════════════════════════
    #  PRIMITIVOS DE MOVIMIENTO (closed-loop — confiables en competencia)
    # ════════════════════════════════════════════════════════════════════════

    def imu_turn(self, degrees):
        """Giro preciso usando el IMU — independiente de patinaje de ruedas."""
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

    def broadcast_state(self):
        """Transmite posición y color al GUI para monitoreo."""
        dist_mm = int(self.drive.distance())
        heading = int(self.hub.imu.heading()) % 360
        try:
            r, g, b = self.COLOR_RGB.get(self.sensor.color(), (0, 0, 0))
        except Exception:
            r, g, b = 0, 0, 0
        self.hub.ble.broadcast((dist_mm, heading, r, g, b))

    # ════════════════════════════════════════════════════════════════════════
    #  PROTOCOLO BLE — PATRÓN DEL MOSAICO
    # ════════════════════════════════════════════════════════════════════════

    def unpack_pattern(self, packed):
        """
        Decodifica int32 packed → lista de 12 Color values.
        Encoding: 2 bits por celda.  Y=0  B=1  G=2  W=3
        """
        color_map = {0: Color.YELLOW, 1: Color.BLUE, 2: Color.GREEN, 3: Color.WHITE}
        pattern = []
        for i in range(12):
            idx = (packed >> (i * 2)) & 0x3
            pattern.append(color_map[idx])
        return pattern

    def pattern_from_fallback(self):
        """Convierte el patrón de strings del fallback a Color values."""
        color_map = {"Y": Color.YELLOW, "B": Color.BLUE,
                     "G": Color.GREEN,  "W": Color.WHITE}
        return [color_map[c] for c in MOSAIC_PATTERN_FALLBACK]

    # ════════════════════════════════════════════════════════════════════════
    #  MISIONES AUTÓNOMAS
    # ════════════════════════════════════════════════════════════════════════

    def run_mission(self, pattern):
        """Ejecuta las 3 misiones en secuencia."""
        self.drive.reset()
        self.hub.imu.reset_heading(0)

        self._mission_tools()
        self._mission_cement()
        self._mission_mosaic(pattern)

        self.drive.stop()
        self.hub.light.on(Color.GREEN)

    # ── Misión 1: Herramientas (45 pts) ──────────────────────────────────────
    def _mission_tools(self):
        """
        Llevar las 3 herramientas a sus zonas destino.

        Herramienta           Destino
        Paleta rectangular  → Área de patrocinadores (blanco con logos)
        Cuenco de cemento   → Espacio de estacionamiento (zona marrón)
        Paleta albañilería  → Zona de inicio (donde empieza el robot)

        PASOS PARA IMPLEMENTAR:
          1. Con mapgui.py, maneja hasta cada herramienta y anota X/Y/Hdg
          2. Llena las constantes DIST_* y ANGLE_* arriba
          3. Descomenta las líneas de movimiento de abajo
          4. Prueba cada segmento por separado (comenta los otros)
        """
        self.hub.light.on(Color.YELLOW)

        # ── Paleta rectangular → Área de patrocinadores ──────────────────
        self.imu_turn(ANGLE_PALETA_RECT)
        self.drive.straight(DIST_PALETA_RECT_MM)
        # self.garra_principal.run_angle(VEL_GARRA, ANGULO_RECOGER)
        # self.drive.straight(-80)
        # self.imu_turn(ANGLE_PATROCINADOR - self.hub.imu.heading())
        # self.drive.straight(DIST_PATROCINADOR_MM)
        # self.garra_principal.run_angle(VEL_GARRA, ANGULO_SOLTAR)
        # self.drive.straight(-80)

        # ── Cuenco de cemento → Espacio de estacionamiento ───────────────
        # self.imu_turn(ANGLE_CUENCO - self.hub.imu.heading())
        # self.drive.straight(DIST_CUENCO_MM)
        # self.garra_principal.run_angle(VEL_GARRA, ANGULO_RECOGER)
        # self.drive.straight(-80)
        # self.imu_turn(ANGLE_PARKING - self.hub.imu.heading())
        # self.drive.straight(DIST_PARKING_MM)
        # self.garra_principal.run_angle(VEL_GARRA, ANGULO_SOLTAR)
        # self.drive.straight(-80)

        # ── Paleta albañilería → Zona de inicio ──────────────────────────
        # self.imu_turn(ANGLE_PALETA_ALB - self.hub.imu.heading())
        # self.drive.straight(DIST_PALETA_ALB_MM)
        # self.garra_principal.run_angle(VEL_GARRA, ANGULO_RECOGER)
        # self.imu_turn(-self.hub.imu.heading())           # regresar a 0°
        # self.drive.straight(-DIST_PALETA_ALB_MM)
        # self.garra_principal.run_angle(VEL_GARRA, ANGULO_SOLTAR)

        self.hub.light.on(Color.GREEN)
        wait(300)

    # ── Misión 2: Cemento (40 pts) ────────────────────────────────────────────
    def _mission_cement(self):
        """
        Llevar bloques de cemento a las zonas objetivo por color.

        Almacenamiento: extremo derecho del campo, 4 secciones por color.
        Destino: zonas objetivo en el centro, color correspondiente.
        1 punto por bloque completamente dentro de la zona correcta.

        ESTRATEGIA RECOMENDADA:
          - Empieza con un solo color para calibrar la ruta
          - Una vez funcione para uno, el loop lo aplica a todos
          - Si la garra aguanta varios bloques, intenta llevar 2-3 a la vez
        """
        self.hub.light.on(Color.BLUE)

        for color in [Color.YELLOW, Color.BLUE, Color.GREEN, Color.WHITE]:
            self._collect_and_deliver_cement(color)

        self.hub.light.on(Color.GREEN)
        wait(300)

    def _collect_and_deliver_cement(self, color):
        """
        Recoge bloques del color dado y los entrega a su zona objetivo.

        IMPLEMENTAR:
          1. Girar hacia el almacenamiento (ANGLE_IR_DERECHA)
          2. Avanzar hasta el color correcto (DIST_CEMENTO_BASE_MM + CEMENTO_OFFSET[color])
          3. Recoger con la garra
          4. Girar hacia la zona objetivo
          5. Avanzar a la zona objetivo del mismo color
          6. Soltar la garra completamente dentro del área
        """
        # self.imu_turn(ANGLE_IR_DERECHA - self.hub.imu.heading())
        # self.drive.straight(DIST_CEMENTO_BASE_MM + CEMENTO_OFFSET[color])
        # self.agarrar_bloques.run_angle(VEL_GARRA, ANGULO_RECOGER)
        # self.drive.straight(-100)
        # self.imu_turn(0 - self.hub.imu.heading())        # regresar al heading base
        # self.drive.straight(DIST_ZONA_OBJ_MM + ZONA_OBJ_OFFSET[color])
        # self.agarrar_bloques.run_angle(VEL_GARRA, ANGULO_SOLTAR)
        # self.drive.straight(-100)
        pass

    # ── Misión 3: Mosaico (120 pts) ───────────────────────────────────────────
    def _mission_mosaic(self, pattern):
        """
        Colocar las 12 baldosas de mosaico según el patrón recibido.

        pattern: lista de 12 Color values
          pattern[0..2]  = fila 0 (superior del marco)
          pattern[3..5]  = fila 1
          pattern[6..8]  = fila 2
          pattern[9..11] = fila 3 (inferior)

        DATOS DEL CAMPO:
          - Tiles: extremo izquierdo (6 por color: Y/B/G/W)
          - Marco: centro del campo, fijo con cinta doble cara
          - Las paredes del marco guían el tile — tolerancia de ~2 cm

        ESTRATEGIA: agrupar por color para minimizar viajes.
        Todos los amarillos primero, luego azules, etc.
        """
        self.hub.light.on(Color.CYAN)

        cells_by_color = {
            Color.YELLOW: [],
            Color.BLUE:   [],
            Color.GREEN:  [],
            Color.WHITE:  [],
        }
        for i in range(12):
            cells_by_color[pattern[i]].append(i)

        for color in [Color.YELLOW, Color.BLUE, Color.GREEN, Color.WHITE]:
            for cell_idx in cells_by_color[color]:
                row = cell_idx // 3
                col = cell_idx % 3
                self._place_mosaic_tile(color, row, col)
                self.broadcast_state()

        self.hub.light.on(Color.GREEN)

    def _place_mosaic_tile(self, color, row, col):
        """
        Recoge 1 tile del color indicado y lo coloca en la celda (row, col).

        row: 0-3 (0=superior)
        col: 0-2 (0=izquierda)

        IMPLEMENTAR:
          1. Ir a la pila de tiles del color (izquierda del campo)
          2. Recoger 1 tile con la garra
          3. Navegar al marco, posicionarse sobre celda (row, col)
          4. Soltar el tile — el marco lo guía al lugar exacto
          5. Retroceder para no arrastrar el tile

        NOTA: Mide DIST_MARCO_MM, PASO_FILA_MM, PASO_COL_MM con el mapper.
        Coloca el robot en la celda 0 (fila 0, col 0) y luego en la celda 2
        (fila 0, col 2) para medir PASO_COL_MM = (X_celda2 - X_celda0) / 2
        """
        # 1. Ir a la pila de tiles del color indicado
        # self.imu_turn(ANGLE_IR_IZQUIERDA - self.hub.imu.heading())
        # self.drive.straight(DIST_TILES_BASE_MM + TILE_OFFSET[color])
        # self.garra_principal.run_angle(VEL_GARRA, ANGULO_RECOGER)
        # self.drive.straight(-100)

        # 2. Ir al marco, celda (row, col)
        # self.imu_turn(ANGLE_IR_DERECHA - self.hub.imu.heading())
        # dist_fila = DIST_MARCO_MM + row * PASO_FILA_MM
        # self.drive.straight(dist_fila)
        # ajuste_col = (col - 1) * PASO_COL_MM   # col 0=-1 col, col 1=0, col 2=+1
        # if ajuste_col != 0:
        #     self.imu_turn(90 if ajuste_col > 0 else -90)
        #     self.drive.straight(abs(ajuste_col))
        #     self.imu_turn(-90 if ajuste_col > 0 else 90)

        # 3. Soltar tile
        # self.garra_principal.run_angle(VEL_GARRA, ANGULO_SOLTAR)
        # self.drive.straight(-80)
        pass

    # ════════════════════════════════════════════════════════════════════════
    #  LOOP PRINCIPAL — BLE + estado de misión
    # ════════════════════════════════════════════════════════════════════════

    def run(self):
        """
        Loop principal. Modos de operación:
          STATE_MANUAL  → Igual que spikemapper.py (para pruebas con el GUI)
          STATE_READY   → Patrón cargado, luz NARANJA, esperando "Iniciar Misión"
          STATE_RUNNING → Ejecutando misión, no acepta comandos de movimiento
        """
        prev_motor_cmd = 0
        prev_turn_cmd  = 0

        # ── Modo fallback: botón izquierdo inicia sin GUI ─────────────────────
        if USE_FALLBACK:
            self.hub.display.text("RDY")
            while Button.LEFT not in self.hub.buttons.pressed():
                wait(50)
            self.hub.display.off()
            self._mosaic_pattern = self.pattern_from_fallback()
            self._state = self.STATE_READY

        while True:
            cmd = self.hub.ble.observe(1)

            if cmd is not None and len(cmd) >= 5:
                speed     = int(cmd[0])
                turn      = int(cmd[1])
                motor_cmd = int(cmd[2])
                motor_val = int(cmd[3])
                turn_cmd  = int(cmd[4])

                # motor_cmd=5: recibir patrón (flanco subida)
                if motor_cmd == 5 and prev_motor_cmd != 5:
                    self._mosaic_pattern = self.unpack_pattern(motor_val)
                    self._state = self.STATE_READY
                    self.hub.light.on(Color.ORANGE)

                # motor_cmd=6: iniciar misión (flanco subida)
                elif motor_cmd == 6 and prev_motor_cmd != 6:
                    if self._state == self.STATE_READY:
                        self._state = self.STATE_RUNNING
                        self.run_mission(self._mosaic_pattern)
                        self._state = self.STATE_MANUAL
                    else:
                        # Parpadeo rojo: no hay patrón cargado
                        self.hub.light.on(Color.RED)
                        wait(400)
                        self.hub.light.on(Color.GREEN)

                # turn_cmd: giro IMU preciso (flanco subida) — útil para pruebas
                elif turn_cmd != 0 and prev_turn_cmd == 0:
                    self.hub.light.on(Color.YELLOW)
                    self.imu_turn(turn_cmd)
                    self.hub.light.on(Color.GREEN if self._state == self.STATE_MANUAL
                                      else Color.ORANGE)

                # motor_cmd=4: drive.straight (flanco subida) — útil para pruebas
                elif motor_cmd == 4 and prev_motor_cmd != 4:
                    self.hub.light.on(Color.CYAN)
                    self.drive.straight(motor_val)
                    self.hub.light.on(Color.GREEN if self._state == self.STATE_MANUAL
                                      else Color.ORANGE)

                # Control continuo (solo en STATE_MANUAL)
                elif motor_cmd not in (4, 5, 6) and turn_cmd == 0:
                    if self._state == self.STATE_MANUAL:
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
                if self._state == self.STATE_MANUAL:
                    self.drive.stop()
                    for m in self.motor_map.values():
                        m.brake()
                prev_motor_cmd = 0
                prev_turn_cmd  = 0

            self.broadcast_state()
            wait(50)


robot = Robot()
robot.run()
