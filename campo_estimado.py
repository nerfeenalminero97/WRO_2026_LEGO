"""
campo_estimado.py  —  WRO 2026 Mosaic Masters
==============================================
Visualizador de posiciones ESTIMADAS del campo basado en:
  • Imagen del mapa: mapa_wro2026.jpg (8000×3871 px ≈ 236×115 cm)
  • Reglas oficiales WRO 2026 Senior
  • Medidas reales del campo: 236 cm × 115 cm

CÓMO USAR:
  1. Corre este script: python campo_estimado.py
  2. Ve las zonas superpuestas en el mapa
  3. Ajusta las constantes de posición (sección "POSICIONES ESTIMADAS")
     hasta que coincidan con lo que ves en el campo real
  4. Copia los valores calibrados a wro_autonomo.py

SISTEMA DE COORDENADAS:
  • (0, 0) = esquina superior-izquierda del campo
  • X crece hacia la DERECHA  (0 → 2360 mm)
  • Y crece hacia ABAJO       (0 → 1150 mm)
  • Heading 0° = mirando hacia ARRIBA (Norte)
  • Heading 90° = mirando hacia la DERECHA (Este)

ROBOT (SPIKE Prime):
  • Diámetro de rueda: 86 mm
  • Circunferencia: π × 86 ≈ 270.2 mm / rotación
  • Axle track: 120 mm
"""

import math
import os
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

# ════════════════════════════════════════════════════════════════
#  DIMENSIONES DEL CAMPO
# ════════════════════════════════════════════════════════════════
FIELD_W_MM = 2360.0
FIELD_H_MM = 1150.0

# Parámetros del robot
WHEEL_DIAM_MM  = 86.0
WHEEL_CIRC_MM  = math.pi * WHEEL_DIAM_MM   # ≈ 270.2 mm/rot
AXLE_TRACK_MM  = 120.0

# ════════════════════════════════════════════════════════════════
#  POSICIONES ESTIMADAS — AJUSTAR CON MEDICIONES REALES
#  Todas las coordenadas en mm desde esquina SUPERIOR-IZQUIERDA
# ════════════════════════════════════════════════════════════════

# ── Robot: posición inicial ──────────────────────────────────────
# Zona de inicio: esquina inferior-izquierda del campo
ROBOT_START_X   = 150    # mm desde borde izquierdo
ROBOT_START_Y   = 1000   # mm desde borde superior
ROBOT_START_HDG = 0      # 0° = mirando hacia arriba (norte)

# ── Herramientas (gray areas, parte inferior del campo) ──────────
# Nota: las 3 plataformas grises están en la zona inferior central
PALETA_RECT_X   = 600    # Llana rectangular
PALETA_RECT_Y   = 965

CUENCO_CEM_X    = 755    # Cuenco de cemento
CUENCO_CEM_Y    = 965

PALETA_ALB_X    = 910    # Paleta de albañilería
PALETA_ALB_Y    = 965

# ── Destinos de las herramientas ─────────────────────────────────
# Área de patrocinadores (blanca con logos, junto a zona de inicio)
SPONSOR_X       = 160
SPONSOR_Y       = 820

# Espacio de estacionamiento (zona marrón, center-bottom)
PARKING_X       = 1010
PARKING_Y       = 770

# Zona de inicio = destino de la paleta de albañilería
# (robot regresa a ROBOT_START_X, ROBOT_START_Y)

# ── Baldosas de mosaico (extremo izquierdo del campo) ────────────
# 6 de cada color, apiladas en la zona izquierda (gris rayada)
# Se accede girando hacia heading=270° (oeste) desde el centro
TILES_X         = 85     # X de todas las pilas de tiles
TILE_Y = {
    "Y": 330,   # Amarillo (Yellow)
    "B": 450,   # Azul     (Blue)
    "G": 570,   # Verde    (Green)
    "W": 690,   # Blanco   (White)
}

# ── Marco de mosaico (centro del campo) ─────────────────────────
# Marco 3×4 celdas; cinta doble cara lo fija al suelo
FRAME_CENTER_X  = 940
FRAME_CENTER_Y  = 415
PASO_COL_MM     = 62     # separación entre columnas (mm)
PASO_FILA_MM    = 62     # separación entre filas (mm)

# Posición de cada celda del marco (fila 0 = superior, col 0 = izquierda)
def celda_xy(fila, col):
    """Devuelve (x_mm, y_mm) del centro de una celda del marco."""
    x = FRAME_CENTER_X + (col - 1) * PASO_COL_MM
    y = FRAME_CENTER_Y + (fila - 1.5) * PASO_FILA_MM
    return x, y

# ── Zonas objetivo del cemento (upper-center, cerca del marco) ───
# 4 zonas de color: amarillo, azul, verde, blanco
# Están en el centro-superior del campo
CEMENT_TARGET_Y = 195
CEMENT_TARGET = {
    "Y": (960,  CEMENT_TARGET_Y),   # Amarillo
    "B": (1090, CEMENT_TARGET_Y),   # Azul
    "G": (1220, CEMENT_TARGET_Y),   # Verde
    "W": (1350, CEMENT_TARGET_Y),   # Blanco
}

# ── Almacenamiento de cemento (extremo derecho del campo) ────────
# 40 elementos en total (10 por color), colocados aleatoriamente
CEMENT_STORE = {
    "Y": (2160, 340),   # Amarillo — arriba
    "B": (2160, 480),   # Azul
    "G": (2160, 610),   # Verde
    "W": (2160, 740),   # Blanco — abajo
}

# ── Barreras (4 en total, zona central) ─────────────────────────
# 2 rojas con bola azul + 2 negras con bola roja
# Posición aproximada alrededor del área de mosaico y cemento
BARRIERS = [
    {"pos": (790,  345),  "tipo": "roja/azul",   "color_fill": "#CC3333", "color_ball": "#3366FF"},
    {"pos": (1090, 300),  "tipo": "roja/azul",   "color_fill": "#CC3333", "color_ball": "#3366FF"},
    {"pos": (800,  540),  "tipo": "negra/roja",  "color_fill": "#333333", "color_ball": "#FF4444"},
    {"pos": (1120, 530),  "tipo": "negra/roja",  "color_fill": "#333333", "color_ball": "#FF4444"},
]

# ════════════════════════════════════════════════════════════════
#  CÁLCULO DE DISTANCIAS Y ROTACIONES
# ════════════════════════════════════════════════════════════════

def dist_mm(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def rotaciones(dist):
    return dist / WHEEL_CIRC_MM

def heading_entre(x1, y1, x2, y2):
    """Heading en grados para ir de (x1,y1) a (x2,y2)."""
    dx = x2 - x1
    dy = y2 - y1
    ang = math.degrees(math.atan2(dx, -dy))
    return ang % 360

# ════════════════════════════════════════════════════════════════
#  RUTA ESTIMADA (waypoints en orden de misión)
# ════════════════════════════════════════════════════════════════
WAYPOINTS = [
    # Nombre                 X             Y         Color      Descripción
    ("Inicio",         ROBOT_START_X, ROBOT_START_Y, "#00FF88", "Posición inicial del robot"),

    # Misión 1: Herramientas
    ("Paleta Rect",    PALETA_RECT_X,  PALETA_RECT_Y,  "#FFD700", "Recoger llana rectangular"),
    ("→ Sponsor",      SPONSOR_X,      SPONSOR_Y,      "#FFD700", "Dejar en área patrocinadores"),
    ("Cuenco",         CUENCO_CEM_X,   CUENCO_CEM_Y,   "#AAAAAA", "Recoger cuenco de cemento"),
    ("→ Parking",      PARKING_X,      PARKING_Y,      "#AAAAAA", "Dejar en estacionamiento"),
    ("Paleta Alb",     PALETA_ALB_X,   PALETA_ALB_Y,   "#FFFFFF", "Recoger paleta albañilería"),
    ("→ Inicio",       ROBOT_START_X,  ROBOT_START_Y + 50, "#FFFFFF", "Dejar en zona de inicio"),

    # Misión 2: Tiles del mosaico (ejemplo: color Amarillo)
    ("Tiles Y",        TILES_X,        TILE_Y["Y"],    "#FFD700", "Recoger tile amarillo"),
    ("Marco 0,0",      *celda_xy(0,0),                 "#FFD700", "Colocar en fila 0, col 0"),
    ("Tiles B",        TILES_X,        TILE_Y["B"],    "#2255CC", "Recoger tile azul"),
    ("Marco 0,1",      *celda_xy(0,1),                 "#2255CC", "Colocar en fila 0, col 1"),

    # Misión 3: Cemento
    ("Cem.Store Y",    *CEMENT_STORE["Y"],              "#FFD700", "Recoger cemento amarillo"),
    ("Cem.Target Y",   *CEMENT_TARGET["Y"],             "#FFD700", "Entregar cemento amarillo"),
    ("Cem.Store B",    *CEMENT_STORE["B"],              "#2255CC", "Recoger cemento azul"),
    ("Cem.Target B",   *CEMENT_TARGET["B"],             "#2255CC", "Entregar cemento azul"),
]

# ════════════════════════════════════════════════════════════════
#  COLORES UI
# ════════════════════════════════════════════════════════════════
BG   = "#0F0F0F"
CARD = "#1A1A1A"
TEXT = "#FFFFFF"
DIM  = "#555555"
CYAN = "#00D4FF"
GRN  = "#00FF88"
AMB  = "#FFB800"
RED  = "#FF4444"
PRP  = "#BB86FC"

# ════════════════════════════════════════════════════════════════
#  APP
# ════════════════════════════════════════════════════════════════
class CampoEstimado:
    MAP_IMG = "mapa_wro2026.jpg"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WRO 2026 — Campo Estimado")
        self.root.configure(bg=BG)
        self.root.geometry("1400x820")

        self._map_img_orig = None
        self._map_photo    = None
        self._map_w = self._map_h = 1
        self._map_ox = self._map_oy = 0
        self._show_zones    = tk.BooleanVar(value=True)
        self._show_route    = tk.BooleanVar(value=True)
        self._show_labels   = tk.BooleanVar(value=True)
        self._show_barriers = tk.BooleanVar(value=True)
        self._show_grid     = tk.BooleanVar(value=True)

        self._build()
        self._load_map()

    # ─── Build UI ────────────────────────────────────────────────
    def _build(self):
        # Toolbar
        tb = tk.Frame(self.root, bg="#111")
        tb.pack(fill="x")
        tk.Label(tb, text="WRO 2026 — Posiciones Estimadas del Campo",
                 bg="#111", fg=TEXT, font=("Helvetica",12,"bold")).pack(side="left",padx=12,pady=6)
        tk.Label(tb, text="Campo: 236 × 115 cm  |  Rueda: ⌀86mm  |  Circunferencia: 270.2mm",
                 bg="#111", fg=DIM, font=("Helvetica",9)).pack(side="right",padx=12)
        tk.Frame(self.root, bg="#252525", height=1).pack(fill="x")

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)

        # ── Mapa ─────────────────────────────────────────────────
        mf = tk.Frame(body, bg="#000")
        mf.pack(side="left", fill="both", expand=True)

        ctrl = tk.Frame(mf, bg="#111")
        ctrl.pack(fill="x")
        for var, lbl in [
            (self._show_zones,    "Zonas"),
            (self._show_route,    "Ruta"),
            (self._show_labels,   "Etiquetas"),
            (self._show_barriers, "Barreras"),
            (self._show_grid,     "Marco"),
        ]:
            tk.Checkbutton(ctrl, text=lbl, variable=var, command=self._redraw,
                           bg="#111", fg=CYAN, selectcolor="#222",
                           activebackground="#111", font=("Helvetica",9)
                           ).pack(side="left", padx=6, pady=4)

        self.cv = tk.Canvas(mf, bg="#1a1a1a", cursor="crosshair",
                            highlightthickness=0)
        self.cv.pack(fill="both", expand=True)
        self.cv.bind("<Configure>", self._on_resize)
        self.cv.bind("<Motion>",    self._on_mouse_move)

        self.coord_lbl = tk.Label(mf, text="X=0mm  Y=0mm",
                                  bg="#111", fg=CYAN, font=("Courier",9))
        self.coord_lbl.pack(fill="x")

        # ── Panel derecho ─────────────────────────────────────────
        pf = tk.Frame(body, bg=BG, width=320)
        pf.pack(side="right", fill="y")
        pf.pack_propagate(False)

        c2 = tk.Canvas(pf, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(pf, orient="vertical", command=c2.yview)
        c2.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        c2.pack(side="left", fill="both", expand=True)
        inn = tk.Frame(c2, bg=BG, width=305)
        c2.create_window((0,0), window=inn, anchor="nw", width=305)
        inn.bind("<Configure>", lambda e: c2.configure(scrollregion=c2.bbox("all")))

        def sep(): tk.Frame(inn, bg="#252525", height=1).pack(fill="x", pady=6)
        def lbl(t, fg=DIM):
            tk.Label(inn, text=t, bg=BG, fg=fg,
                     font=("Helvetica",8,"bold")).pack(anchor="w",padx=8,pady=(4,2))

        lbl("📐 DISTANCIAS ESTIMADAS (robot en inicio)", CYAN)

        distances = [
            ("Inicio → Paleta Rect",
             dist_mm(ROBOT_START_X, ROBOT_START_Y, PALETA_RECT_X, PALETA_RECT_Y)),
            ("Paleta Rect → Sponsor",
             dist_mm(PALETA_RECT_X, PALETA_RECT_Y, SPONSOR_X, SPONSOR_Y)),
            ("Inicio → Cuenco",
             dist_mm(ROBOT_START_X, ROBOT_START_Y, CUENCO_CEM_X, CUENCO_CEM_Y)),
            ("Cuenco → Parking",
             dist_mm(CUENCO_CEM_X, CUENCO_CEM_Y, PARKING_X, PARKING_Y)),
            ("Inicio → Paleta Alb",
             dist_mm(ROBOT_START_X, ROBOT_START_Y, PALETA_ALB_X, PALETA_ALB_Y)),
            ("─── Tiles ───", 0),
            ("Inicio → Tiles Y",
             dist_mm(ROBOT_START_X, ROBOT_START_Y, TILES_X, TILE_Y["Y"])),
            ("Inicio → Tiles B",
             dist_mm(ROBOT_START_X, ROBOT_START_Y, TILES_X, TILE_Y["B"])),
            ("Tiles Y → Marco centro",
             dist_mm(TILES_X, TILE_Y["Y"], FRAME_CENTER_X, FRAME_CENTER_Y)),
            ("─── Cemento ───", 0),
            ("Inicio → Store Y",
             dist_mm(ROBOT_START_X, ROBOT_START_Y, *CEMENT_STORE["Y"])),
            ("Store Y → Target Y",
             dist_mm(*CEMENT_STORE["Y"], *CEMENT_TARGET["Y"])),
            ("Store B → Target B",
             dist_mm(*CEMENT_STORE["B"], *CEMENT_TARGET["B"])),
        ]

        for name, d in distances:
            if d == 0:
                lbl(name, AMB)
                continue
            rot = rotaciones(d)
            hdg = heading_entre(ROBOT_START_X, ROBOT_START_Y,
                                PALETA_RECT_X, PALETA_RECT_Y)
            row = tk.Frame(inn, bg=CARD)
            row.pack(fill="x", padx=8, pady=1)
            tk.Label(row, text=name, bg=CARD, fg=TEXT,
                     font=("Helvetica",8), anchor="w",
                     width=22).pack(side="left", padx=4, pady=2)
            tk.Label(row, text=f"{d:.0f}mm", bg=CARD, fg=CYAN,
                     font=("Courier",8), width=7).pack(side="left")
            tk.Label(row, text=f"{rot:.2f}rot", bg=CARD, fg=AMB,
                     font=("Courier",8), width=7).pack(side="left")

        sep()
        lbl("🗺 WAYPOINTS DE LA RUTA", CYAN)

        for i, (name, x, y, color, desc) in enumerate(WAYPOINTS):
            row = tk.Frame(inn, bg=CARD)
            row.pack(fill="x", padx=8, pady=1)
            dot = tk.Canvas(row, width=12, height=12, bg=CARD,
                            highlightthickness=0)
            dot.create_oval(1,1,11,11, fill=color, outline="#555")
            dot.pack(side="left", padx=4, pady=3)
            tk.Label(row, text=f"{i+1:2d}. {name:14s} ({x:.0f},{y:.0f})",
                     bg=CARD, fg=TEXT, font=("Courier",8),
                     anchor="w").pack(side="left")

        sep()
        lbl("📏 MARCO DE MOSAICO (celdas estimadas)", CYAN)
        for fila in range(4):
            row = tk.Frame(inn, bg=BG)
            row.pack(fill="x", padx=8, pady=1)
            for col in range(3):
                cx, cy = celda_xy(fila, col)
                tk.Label(row, text=f"[{fila},{col}]\n({cx:.0f},{cy:.0f})",
                         bg=CARD, fg=DIM, font=("Courier",7),
                         width=9, relief="flat", pady=2).pack(side="left", padx=1)

        sep()
        lbl("⚙️  PARÁMETROS DEL ROBOT", CYAN)
        params = [
            ("Ø rueda",      f"{WHEEL_DIAM_MM} mm"),
            ("Circunf.",     f"{WHEEL_CIRC_MM:.1f} mm"),
            ("Axle track",   f"{AXLE_TRACK_MM} mm"),
            ("1 rotación",   f"{WHEEL_CIRC_MM:.1f} mm"),
            ("Campo W",      f"{FIELD_W_MM:.0f} mm"),
            ("Campo H",      f"{FIELD_H_MM:.0f} mm"),
        ]
        for k, v in params:
            row = tk.Frame(inn, bg=CARD)
            row.pack(fill="x", padx=8, pady=1)
            tk.Label(row, text=k, bg=CARD, fg=DIM,
                     font=("Helvetica",8), width=12, anchor="w").pack(side="left", padx=4, pady=2)
            tk.Label(row, text=v, bg=CARD, fg=CYAN,
                     font=("Courier",8)).pack(side="left")

    # ─── Map loading ─────────────────────────────────────────────
    def _load_map(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.MAP_IMG)
        try:
            self._map_img_orig = Image.open(path)
        except Exception as e:
            print(f"[Map] {e}")
            self._map_img_orig = None
        self.root.after(100, self._render_map)

    def _on_resize(self, event=None):
        self._render_map()

    def _render_map(self):
        w = self.cv.winfo_width()
        h = self.cv.winfo_height()
        if w < 10 or h < 10:
            self.root.after(50, self._render_map)
            return

        if self._map_img_orig:
            iw, ih = self._map_img_orig.size
            scale = min(w / iw, h / ih)
            nw = int(iw * scale)
            nh = int(ih * scale)
            img = self._map_img_orig.resize((nw, nh), Image.LANCZOS)
            self._map_photo = ImageTk.PhotoImage(img)
            self._map_w = nw
            self._map_h = nh
        else:
            self._map_photo = None
            self._map_w = w
            self._map_h = h
        self._redraw()

    # ─── Coordinate conversions ──────────────────────────────────
    def _mm_to_px(self, x_mm, y_mm):
        px = int(x_mm / FIELD_W_MM * self._map_w)
        py = int(y_mm / FIELD_H_MM * self._map_h)
        return px + self._map_ox, py + self._map_oy

    def _px_to_mm(self, px, py):
        x = (px - self._map_ox) / self._map_w * FIELD_W_MM
        y = (py - self._map_oy) / self._map_h * FIELD_H_MM
        return x, y

    # ─── Mouse ───────────────────────────────────────────────────
    def _on_mouse_move(self, event):
        x, y = self._px_to_mm(event.x, event.y)
        rot = dist_mm(ROBOT_START_X, ROBOT_START_Y, x, y) / WHEEL_CIRC_MM
        hdg = heading_entre(ROBOT_START_X, ROBOT_START_Y, x, y)
        self.coord_lbl.config(
            text=f"X={x:.0f}mm  Y={y:.0f}mm  |  Desde inicio: {dist_mm(ROBOT_START_X,ROBOT_START_Y,x,y):.0f}mm = {rot:.2f}rot  Hdg={hdg:.0f}°")

    # ─── Drawing ─────────────────────────────────────────────────
    def _redraw(self):
        cv = self.cv
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()

        cv.create_rectangle(0, 0, w, h, fill="#000", outline="")

        if self._map_photo:
            self._map_ox = (w - self._map_w) // 2
            self._map_oy = (h - self._map_h) // 2
            cv.create_image(self._map_ox, self._map_oy,
                            anchor="nw", image=self._map_photo)
        else:
            self._map_ox = 0; self._map_oy = 0
            cv.create_text(w//2, h//2, text="mapa_wro2026.jpg no encontrado",
                           fill=DIM, font=("Helvetica",12))

        if self._show_zones.get():
            self._draw_zones()
        if self._show_grid.get():
            self._draw_mosaic_frame()
        if self._show_barriers.get():
            self._draw_barriers()
        if self._show_route.get():
            self._draw_route()

    def _draw_zones(self):
        cv = self.cv

        def rect_zone(x1_mm, y1_mm, x2_mm, y2_mm, color, label, alpha_fill=True):
            x1, y1 = self._mm_to_px(x1_mm, y1_mm)
            x2, y2 = self._mm_to_px(x2_mm, y2_mm)
            cv.create_rectangle(x1, y1, x2, y2,
                                 outline=color, width=2, dash=(6,3))
            if self._show_labels.get():
                cv.create_text((x1+x2)//2, (y1+y2)//2, text=label,
                               fill=color, font=("Helvetica",7,"bold"))

        def circle_zone(x_mm, y_mm, r_mm, color, label, r_px=None):
            px, py = self._mm_to_px(x_mm, y_mm)
            r = r_px or max(8, int(r_mm / FIELD_W_MM * self._map_w))
            cv.create_oval(px-r, py-r, px+r, py+r,
                           fill=color+"44", outline=color, width=2)
            if self._show_labels.get():
                cv.create_text(px, py, text=label,
                               fill="#FFF", font=("Helvetica",7,"bold"))

        # Zona de inicio
        rect_zone(10, 860, 290, 1140, "#00FF88", "INICIO")

        # Área de patrocinadores
        rect_zone(30, 700, 290, 860, "#FFB800", "SPONSOR")

        # Herramientas
        circle_zone(PALETA_RECT_X, PALETA_RECT_Y, 50, "#FF9944", "P.RECT", 18)
        circle_zone(CUENCO_CEM_X,  CUENCO_CEM_Y,  50, "#AAAAAA", "CUENCO", 18)
        circle_zone(PALETA_ALB_X,  PALETA_ALB_Y,  50, "#DDDDDD", "P.ALB",  18)

        # Parking (zona marrón)
        rect_zone(650, 600, 1360, 940, "#CC8844", "PARKING")

        # Tiles de mosaico (izquierdo)
        for key, (clr, yy) in [("Y","#FFD700"),("B","#2255CC"),
                                 ("G","#22AA44"),("W","#DDDDDD")]:
            ypos = TILE_Y[key]
            px, py = self._mm_to_px(TILES_X, ypos)
            cv.create_rectangle(px-12, py-35, px+12, py+35,
                                 fill=clr+"88", outline=clr, width=2)
            if self._show_labels.get():
                cv.create_text(px, py, text=key, fill="#FFF",
                               font=("Helvetica",8,"bold"))

        # Zonas objetivo del cemento
        for key, (cx, cy) in CEMENT_TARGET.items():
            colors = {"Y":"#FFD700","B":"#2255CC","G":"#22AA44","W":"#DDDDDD"}
            px, py = self._mm_to_px(cx, cy)
            cv.create_rectangle(px-20, py-20, px+20, py+20,
                                 fill=colors[key]+"66", outline=colors[key], width=2)
            if self._show_labels.get():
                cv.create_text(px, py+28, text=f"TGT-{key}",
                               fill=colors[key], font=("Helvetica",7))

        # Almacenamiento de cemento (derecho)
        rect_zone(2000, 200, 2350, 850, "#888888", "CEMENTO\nSTORE")
        for key, (cx, cy) in CEMENT_STORE.items():
            colors = {"Y":"#FFD700","B":"#2255CC","G":"#22AA44","W":"#DDDDDD"}
            px, py = self._mm_to_px(cx, cy)
            cv.create_rectangle(px-28, py-14, px+28, py+14,
                                 fill=colors[key]+"88", outline=colors[key], width=2)
            if self._show_labels.get():
                cv.create_text(px, py, text=f"STR-{key}",
                               fill="#FFF", font=("Helvetica",7,"bold"))

        # Robot inicio
        px, py = self._mm_to_px(ROBOT_START_X, ROBOT_START_Y)
        cv.create_polygon(
            px, py-14, px-10, py+10, px+10, py+10,
            fill=AMB, outline="#FFF", width=2
        )
        if self._show_labels.get():
            cv.create_text(px, py+22, text="ROBOT\nINICIO",
                           fill=AMB, font=("Helvetica",7,"bold"), justify="center")

    def _draw_mosaic_frame(self):
        cv = self.cv
        # Dibujar las 12 celdas del marco (4 filas × 3 cols)
        for fila in range(4):
            for col in range(3):
                cx, cy = celda_xy(fila, col)
                px, py = self._mm_to_px(cx, cy)
                half = max(6, int(PASO_COL_MM / 2 / FIELD_W_MM * self._map_w))
                cv.create_rectangle(px-half, py-half, px+half, py+half,
                                     outline=CYAN, width=2, fill="#00CCFF22")
                if self._show_labels.get():
                    cv.create_text(px, py, text=f"{fila},{col}",
                                   fill=CYAN, font=("Helvetica",6))

        # Borde exterior del marco
        fx1, fy1 = celda_xy(0, 0)
        fx2, fy2 = celda_xy(3, 2)
        p1 = self._mm_to_px(fx1 - PASO_COL_MM//2, fy1 - PASO_FILA_MM//2)
        p2 = self._mm_to_px(fx2 + PASO_COL_MM//2, fy2 + PASO_FILA_MM//2)
        cv.create_rectangle(*p1, *p2, outline="#00CCFF", width=3, dash=(8,4))
        if self._show_labels.get():
            mx = (p1[0] + p2[0]) // 2
            cv.create_text(mx, p1[1] - 10, text="MARCO MOSAICO",
                           fill=CYAN, font=("Helvetica",8,"bold"))

    def _draw_barriers(self):
        cv = self.cv
        for b in BARRIERS:
            px, py = self._mm_to_px(*b["pos"])
            r = max(8, int(40 / FIELD_W_MM * self._map_w))
            cv.create_oval(px-r, py-r, px+r, py+r,
                           fill=b["color_fill"]+"99", outline=b["color_fill"], width=2)
            # bola encima
            rb = max(5, int(20 / FIELD_W_MM * self._map_w))
            cv.create_oval(px-rb, py-r-rb*2, px+rb, py-r,
                           fill=b["color_ball"], outline="#FFF", width=1)
            if self._show_labels.get():
                cv.create_text(px, py+r+10, text="BARRERA",
                               fill=b["color_fill"], font=("Helvetica",6))

    def _draw_route(self):
        cv = self.cv
        coords = [(wp[1], wp[2], wp[3]) for wp in WAYPOINTS]

        # Líneas de la ruta
        for i in range(1, len(coords)):
            x1, y1 = self._mm_to_px(coords[i-1][0], coords[i-1][1])
            x2, y2 = self._mm_to_px(coords[i][0],   coords[i][1])
            cv.create_line(x1, y1, x2, y2,
                           fill="#00AAAA", width=2, dash=(5,3), arrow="last",
                           arrowshape=(8,10,4))

        # Círculos de waypoints
        for i, (x_mm, y_mm, color) in enumerate(coords):
            px, py = self._mm_to_px(x_mm, y_mm)
            r = 8
            cv.create_oval(px-r, py-r, px+r, py+r,
                           fill=color, outline="#FFF", width=2)
            if self._show_labels.get():
                cv.create_text(px, py, text=str(i+1),
                               fill="#000", font=("Helvetica",7,"bold"))


# ════════════════════════════════════════════════════════════════
#  REPORTE DE CONSOLA
# ════════════════════════════════════════════════════════════════
def print_report():
    print("\n" + "═"*60)
    print("  WRO 2026 — Posiciones Estimadas del Campo")
    print("  Campo: 236 × 115 cm | Rueda: ⌀86mm | Circ: 270.2mm")
    print("═"*60)

    sections = [
        ("🔧 HERRAMIENTAS", [
            ("Paleta rectangular", PALETA_RECT_X, PALETA_RECT_Y),
            ("Cuenco de cemento",  CUENCO_CEM_X,  CUENCO_CEM_Y),
            ("Paleta albañilería", PALETA_ALB_X,  PALETA_ALB_Y),
        ]),
        ("🎯 DESTINOS", [
            ("Área patrocinadores", SPONSOR_X, SPONSOR_Y),
            ("Espacio parking",     PARKING_X, PARKING_Y),
            ("Zona de inicio",      ROBOT_START_X, ROBOT_START_Y),
        ]),
        ("🟦 TILES (Almacenamiento izquierdo)", [
            ("Tiles Amarillo", TILES_X, TILE_Y["Y"]),
            ("Tiles Azul",     TILES_X, TILE_Y["B"]),
            ("Tiles Verde",    TILES_X, TILE_Y["G"]),
            ("Tiles Blanco",   TILES_X, TILE_Y["W"]),
        ]),
        ("🧱 MARCO DE MOSAICO (celdas)", [
            (f"Celda {f},{c}", *celda_xy(f,c))
            for f in range(4) for c in range(3)
        ]),
        ("🏗 ZONAS OBJETIVO DEL CEMENTO", [
            (f"Target {k}", x, y) for k,(x,y) in CEMENT_TARGET.items()
        ]),
        ("📦 ALMACENAMIENTO CEMENTO (derecho)", [
            (f"Store {k}", x, y) for k,(x,y) in CEMENT_STORE.items()
        ]),
    ]

    for title, items in sections:
        print(f"\n{title}")
        for name, x, y in items:
            d = dist_mm(ROBOT_START_X, ROBOT_START_Y, x, y)
            r = rotaciones(d)
            h = heading_entre(ROBOT_START_X, ROBOT_START_Y, x, y)
            print(f"  {name:<28} ({x:5.0f}, {y:5.0f}) mm  "
                  f"→ {d:6.0f}mm / {r:.2f}rot  Hdg≈{h:5.1f}°")

    print("\n" + "═"*60 + "\n")


# ════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print_report()
    root = tk.Tk()
    app  = CampoEstimado(root)
    root.mainloop()
