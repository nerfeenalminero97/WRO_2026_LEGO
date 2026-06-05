# campo_simulador.py  —  WRO 2026 Mosaic Masters
#
# USO:
#   ► Modo ZONA   — selecciona una zona del menú, luego ARRASTRA en el campo
#                   para definir Parking, Marco de Mosaico y Dianas.
#   ► Modo RUTA   — click izquierdo agrega puntos de ruta (polilinea).
#                   Click derecho elimina el último punto.
#                   Usa puntos intermedios para rodear obstáculos.
#
# python3 campo_simulador.py

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import math

# ════════════════════════════════════════════════════════════════════════
#  DIMENSIONES DEL CAMPO
# ════════════════════════════════════════════════════════════════════════
FIELD_W  = 2360
FIELD_H  = 1150
CANVAS_W = 1100
CANVAS_H = int(CANVAS_W * FIELD_H / FIELD_W)
SCALE    = CANVAS_W / FIELD_W

# ════════════════════════════════════════════════════════════════════════
#  ZONAS FIJAS (posiciones conocidas / no cambian)
# ════════════════════════════════════════════════════════════════════════
FIXED_ZONES = [
    # label, x1, y1, x2, y2 (mm), fill, text_color
    ("Zona Inicio\n(Paleta→aquí)",        0,    0,  310,  310, "#B3E5FC", "#0D47A1"),
    ("Patrocinadores\n(Llana→aquí)",     370,    0,  710,  220, "#FFFFFF", "#1565C0"),
    # pickups herramientas
    ("Llana rect.\n(pickup)",            800,    0, 1020,  210, "#78909C", "#FFFFFF"),
    ("Cuenco cem.\n(pickup)",           1090,    0, 1310,  210, "#78909C", "#FFFFFF"),
    ("Paleta alb.\n(pickup)",           1490,    0, 1710,  210, "#78909C", "#FFFFFF"),
    # almacenamiento cemento (derecha) — fijo
    ("Cemento\nBlanco",                 2130,   70, 2360,  370, "#F5F5F5", "#424242"),
    ("Cemento\nVerde",                  2130,  380, 2360,  630, "#A5D6A7", "#2E7D32"),
    ("Cemento\nAzul",                   2130,  640, 2360,  890, "#90CAF9", "#1565C0"),
    ("Cemento\nAmarillo",               2130,  900, 2360, 1100, "#FFF176", "#F57F17"),
    # baldosas (izquierda) — fijo
    ("Baldosas\nAmarillo",              180,  380,  470,  545, "#FFF176", "#F57F17"),
    ("Baldosas\nAzul",                  180,  555,  470,  720, "#90CAF9", "#1565C0"),
    ("Baldosas\nVerde",                 180,  730,  470,  895, "#A5D6A7", "#2E7D32"),
    ("Baldosas\nBlanco",                180,  905,  470, 1060, "#F5F5F5", "#424242"),
]

# ════════════════════════════════════════════════════════════════════════
#  ZONAS DEFINIBLES POR EL USUARIO (arrastra para dibujarlas)
# ════════════════════════════════════════════════════════════════════════
USER_ZONE_TYPES = [
    ("Parking / Estacionamiento", "#8D6E63", "#FFFFFF"),
    ("Marco de Mosaico",          "#E3F2FD", "#0D47A1"),
    ("Diana Blanco",              "#EEEEEE", "#424242"),
    ("Diana Verde",               "#C8E6C9", "#2E7D32"),
    ("Diana Azul",                "#BBDEFB", "#1565C0"),
    ("Diana Amarillo",            "#FFF9C4", "#F57F17"),
]

# Barreras (obstáculos)
BARRIERS = [(860, 400), (860, 1010), (1560, 400), (1560, 1010)]

# ════════════════════════════════════════════════════════════════════════
#  CONVERSIÓN mm ↔ px
# ════════════════════════════════════════════════════════════════════════
def mm_to_px(x, y):
    return x * SCALE, CANVAS_H - y * SCALE

def px_to_mm(px, py):
    return round(px / SCALE), round((CANVAS_H - py) / SCALE)

def leg_info(ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    dist = math.sqrt(dx*dx + dy*dy)
    heading = math.degrees(math.atan2(-dy, dx)) if dist > 0 else 0
    return round(heading, 1), round(dist)


# ════════════════════════════════════════════════════════════════════════
#  APP
# ════════════════════════════════════════════════════════════════════════
class Simulador(tk.Tk):
    WP_R = 7

    def __init__(self):
        super().__init__()
        self.title("WRO 2026 — Simulador de Campo")
        self.resizable(True, True)

        # Estado
        self.mode       = tk.StringVar(value="ruta")   # "ruta" | "zona"
        self.zone_type  = tk.StringVar(value=USER_ZONE_TYPES[0][0])
        self.wp_type    = tk.StringVar(value="destino") # "destino" | "intermedio"

        self.waypoints  = []   # [(x,y,label,tipo), ...]
        self.user_zones = []   # [(label, x1,y1,x2,y2, fill, fg), ...]

        # Drag para zona
        self._drag_start = None

        self._build_ui()
        self._redraw()

    # ── Layout ────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Barra de herramientas
        toolbar = tk.Frame(self, bg="#263238", pady=4)
        toolbar.pack(fill=tk.X)

        tk.Label(toolbar, text="MODO:", fg="white", bg="#263238",
                 font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=(10,2))

        tk.Radiobutton(toolbar, text="✏ Trazar Ruta", variable=self.mode,
                       value="ruta", bg="#263238", fg="white",
                       selectcolor="#37474F", activebackground="#263238",
                       font=("Helvetica", 10, "bold"),
                       command=self._on_mode_change).pack(side=tk.LEFT, padx=4)

        tk.Radiobutton(toolbar, text="⬜ Definir Zona", variable=self.mode,
                       value="zona", bg="#263238", fg="white",
                       selectcolor="#37474F", activebackground="#263238",
                       font=("Helvetica", 10, "bold"),
                       command=self._on_mode_change).pack(side=tk.LEFT, padx=4)

        tk.Label(toolbar, text=" | Zona:", fg="#B0BEC5", bg="#263238").pack(side=tk.LEFT)
        self.combo_zone = ttk.Combobox(toolbar, textvariable=self.zone_type, width=22,
                                        state="disabled",
                                        values=[z[0] for z in USER_ZONE_TYPES])
        self.combo_zone.pack(side=tk.LEFT, padx=4)

        tk.Label(toolbar, text=" | Punto:", fg="#B0BEC5", bg="#263238").pack(side=tk.LEFT)
        tk.Radiobutton(toolbar, text="● Destino", variable=self.wp_type,
                       value="destino", bg="#263238", fg="#EF9A9A",
                       selectcolor="#37474F", activebackground="#263238").pack(side=tk.LEFT)
        tk.Radiobutton(toolbar, text="◌ Intermedio", variable=self.wp_type,
                       value="intermedio", bg="#263238", fg="#80CBC4",
                       selectcolor="#37474F", activebackground="#263238").pack(side=tk.LEFT)

        tk.Button(toolbar, text="Borrar último", bg="#E57373", fg="white",
                  command=self._remove_last).pack(side=tk.RIGHT, padx=4)
        tk.Button(toolbar, text="Limpiar ruta", bg="#FF8F00", fg="white",
                  command=self._clear_route).pack(side=tk.RIGHT, padx=4)
        tk.Button(toolbar, text="Borrar zonas", bg="#546E7A", fg="white",
                  command=self._clear_zones).pack(side=tk.RIGHT, padx=4)
        tk.Button(toolbar, text="Exportar código", bg="#388E3C", fg="white",
                  command=self._export).pack(side=tk.RIGHT, padx=4)

        # Instrucciones
        self.lbl_instruc = tk.Label(self, bg="#37474F", fg="white", pady=3,
                                     font=("Helvetica", 9))
        self.lbl_instruc.pack(fill=tk.X)
        self._update_instruc()

        # Cuerpo principal
        body = tk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)

        # Canvas
        self.canvas = tk.Canvas(body, width=CANVAS_W, height=CANVAS_H,
                                 bg="#BDBDBD", cursor="crosshair")
        self.canvas.pack(side=tk.LEFT)
        self.canvas.bind("<Button-1>",        self._on_click)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<Button-2>",        self._on_right)
        self.canvas.bind("<Button-3>",        self._on_right)
        self.canvas.bind("<Motion>",          self._on_hover)

        # Panel derecho
        panel = tk.Frame(body, width=320, bg="#ECEFF1")
        panel.pack(side=tk.RIGHT, fill=tk.Y)
        panel.pack_propagate(False)

        tk.Label(panel, text="RUTA Y DISTANCIAS", bg="#1565C0", fg="white",
                 font=("Helvetica", 10, "bold"), pady=4).pack(fill=tk.X)

        self.txt = scrolledtext.ScrolledText(panel, font=("Courier", 8),
                                              height=22, wrap=tk.WORD)
        self.txt.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        # Coordenadas en tiempo real
        self.lbl_xy = tk.Label(self, text="", font=("Courier", 10),
                                bg="#F5F5F5", anchor=tk.W)
        self.lbl_xy.pack(fill=tk.X)

    # ── Modos ─────────────────────────────────────────────────────────────

    def _on_mode_change(self):
        if self.mode.get() == "zona":
            self.combo_zone.config(state="readonly")
            self.canvas.config(cursor="crosshair")
        else:
            self.combo_zone.config(state="disabled")
            self.canvas.config(cursor="crosshair")
        self._update_instruc()

    def _update_instruc(self):
        if self.mode.get() == "ruta":
            txt = ("  MODO RUTA — Click izquierdo: agregar punto  |  "
                   "Click derecho: borrar último  |  "
                   "Cambia entre Destino / Intermedio en la barra de arriba")
        else:
            txt = ("  MODO ZONA — Selecciona la zona en el menú, "
                   "luego ARRASTRA sobre el campo para dibujarla  |  "
                   "Click derecho sobre zona: eliminarla")
        self.lbl_instruc.config(text=txt)

    # ── Eventos de canvas ─────────────────────────────────────────────────

    def _on_click(self, e):
        if self.mode.get() == "ruta":
            x, y = px_to_mm(e.x, e.y)
            if 0 <= x <= FIELD_W and 0 <= y <= FIELD_H:
                tipo = self.wp_type.get()
                n = len(self.waypoints)
                label = f"WP{n}" if tipo == "intermedio" else f"P{n}"
                self.waypoints.append((x, y, label, tipo))
                self._redraw()
        else:
            # Inicio de drag para zona
            self._drag_start = (e.x, e.y)

    def _on_drag(self, e):
        if self.mode.get() == "zona" and self._drag_start:
            self._redraw()
            sx, sy = self._drag_start
            self.canvas.create_rectangle(sx, sy, e.x, e.y,
                                          outline="#E91E63", width=2, dash=(4,2),
                                          tags="drag_preview")

    def _on_release(self, e):
        if self.mode.get() != "zona" or not self._drag_start:
            return
        sx, sy = self._drag_start
        self._drag_start = None

        # Mínimo 20px de arrastre para crear zona
        if abs(e.x - sx) < 20 or abs(e.y - sy) < 20:
            return

        x1, y1 = px_to_mm(min(sx, e.x), min(sy, e.y))
        x2, y2 = px_to_mm(max(sx, e.x), max(sy, e.y))
        # En coordenadas campo Y2>Y1 siempre
        y_lo, y_hi = min(y1, y2), max(y1, y2)

        zname = self.zone_type.get()
        # Buscar color para este tipo
        fill, fg = "#CFD8DC", "#000000"
        for name, f, t in USER_ZONE_TYPES:
            if name == zname:
                fill, fg = f, t
                break

        # Si ya existe esa zona, reemplazarla
        self.user_zones = [(l, a, b, c, d, f2, t2)
                           for (l, a, b, c, d, f2, t2) in self.user_zones
                           if l != zname]
        self.user_zones.append((zname, x1, y_lo, x2, y_hi, fill, fg))
        self._redraw()

    def _on_right(self, e):
        if self.mode.get() == "ruta":
            self._remove_last()
        else:
            # Eliminar zona bajo el cursor
            xm, ym = px_to_mm(e.x, e.y)
            self.user_zones = [(l, a, b, c, d, f, t)
                               for (l, a, b, c, d, f, t) in self.user_zones
                               if not (a <= xm <= c and b <= ym <= d)]
            self._redraw()

    def _on_hover(self, e):
        x, y = px_to_mm(e.x, e.y)
        self.lbl_xy.config(text=f"   X = {x:5d} mm   Y = {y:5d} mm")

    # ── Dibujo ────────────────────────────────────────────────────────────

    def _redraw(self):
        self.canvas.delete("all")

        # Fondo
        self.canvas.create_rectangle(0, 0, CANVAS_W, CANVAS_H,
                                      fill="#E0E0E0", outline="")

        # Zonas fijas
        for (lbl, x1, y1, x2, y2, fill, fg) in FIXED_ZONES:
            px1, py1 = mm_to_px(x1, y2)
            px2, py2 = mm_to_px(x2, y1)
            self.canvas.create_rectangle(px1, py1, px2, py2,
                                          fill=fill, outline="#546E7A", width=1)
            self.canvas.create_text((px1+px2)/2, (py1+py2)/2,
                                     text=lbl, font=("Helvetica", 7),
                                     fill=fg, justify=tk.CENTER)

        # Zonas definidas por usuario
        for (lbl, x1, y1, x2, y2, fill, fg) in self.user_zones:
            px1, py1 = mm_to_px(x1, y2)
            px2, py2 = mm_to_px(x2, y1)
            self.canvas.create_rectangle(px1, py1, px2, py2,
                                          fill=fill, outline="#E91E63",
                                          width=2, stipple="gray12")
            self.canvas.create_text((px1+px2)/2, (py1+py2)/2,
                                     text=lbl, font=("Helvetica", 8, "bold"),
                                     fill=fg, justify=tk.CENTER)
            # Coordenadas en esquina
            self.canvas.create_text(px1+4, py2-4,
                                     text=f"({x1},{y1})", font=("Helvetica", 6),
                                     fill="#880E4F", anchor=tk.SW)
            self.canvas.create_text(px2-4, py1+4,
                                     text=f"({x2},{y2})", font=("Helvetica", 6),
                                     fill="#880E4F", anchor=tk.NE)

        # Barreras
        BR = 65 * SCALE
        for (bx, by) in BARRIERS:
            px, py = mm_to_px(bx, by)
            self.canvas.create_oval(px-BR, py-BR, px+BR, py+BR,
                                     fill="#EF9A9A", outline="#B71C1C",
                                     width=2, stipple="gray50")
            self.canvas.create_text(px, py, text="⛔", font=("Helvetica", 9))

        # Borde del campo
        self.canvas.create_rectangle(0, 0, CANVAS_W-1, CANVAS_H-1,
                                      outline="#000000", width=2)

        # Escala visual
        self._draw_scale()

        # Ruta (polilinea)
        self._draw_route()

        self._update_panel()

    def _draw_scale(self):
        px1, py = mm_to_px(50, 25)
        px2, _  = mm_to_px(550, 25)
        self.canvas.create_line(px1, py, px2, py, fill="#333", width=2)
        for px in (px1, px2):
            self.canvas.create_line(px, py-4, px, py+4, fill="#333", width=2)
        self.canvas.create_text((px1+px2)/2, py+9,
                                  text="500 mm", font=("Helvetica", 7))

    def _draw_route(self):
        wps = self.waypoints
        if not wps:
            return

        # Líneas de ruta (polilinea quebrada)
        for i in range(len(wps) - 1):
            ax, ay, al, at = wps[i]
            bx, by, bl, bt = wps[i+1]
            pax, pay = mm_to_px(ax, ay)
            pbx, pby = mm_to_px(bx, by)
            color = "#E91E63"
            self.canvas.create_line(pax, pay, pbx, pby,
                                     fill=color, width=2,
                                     arrow=tk.LAST, arrowshape=(10, 12, 4))
            # Etiqueta del tramo
            h, d = leg_info(ax, ay, bx, by)
            mx, my = (pax+pbx)/2, (pay+pby)/2
            self.canvas.create_text(mx, my - 8,
                                     text=f"{d}mm / {h}°",
                                     font=("Helvetica", 7, "bold"),
                                     fill="#880E4F")

        # Puntos de waypoint
        for i, (wx, wy, wlbl, wtyp) in enumerate(wps):
            px, py = mm_to_px(wx, wy)
            if i == 0:
                fill, outline = "#1565C0", "white"       # inicio = azul
            elif wtyp == "intermedio":
                fill, outline = "#00BCD4", "#004D40"     # intermedio = cyan
            else:
                fill, outline = "#E91E63", "white"       # destino = rosa

            r = self.WP_R if wtyp != "intermedio" else 5
            self.canvas.create_oval(px-r, py-r, px+r, py+r,
                                     fill=fill, outline=outline, width=2)
            self.canvas.create_text(px, py,
                                     text=str(i), font=("Helvetica", 7, "bold"),
                                     fill="white")
            self.canvas.create_text(px + r + 3, py - r,
                                     text=f"{wlbl}\n({wx},{wy})",
                                     font=("Helvetica", 6), fill="#212121",
                                     anchor=tk.W)

    # ── Panel de información ──────────────────────────────────────────────

    def _update_panel(self):
        wps = self.waypoints
        lines = []

        if not wps:
            lines.append("Sin waypoints.\n")
            lines.append("Modo RUTA: click izquierdo\npara agregar puntos.")
        else:
            lines.append(f"{'#':>2}  {'Tipo':>10}  {'Nombre':<10}  {'X':>5}  {'Y':>5}")
            lines.append("─" * 44)
            for i, (x, y, lbl, typ) in enumerate(wps):
                lines.append(f"{i:>2}  {typ:>10}  {lbl:<10}  {x:>5}  {y:>5}")

            if len(wps) > 1:
                lines.append("")
                lines.append(f"{'Tramo':<22}  {'Hdg':>7}  {'Dist':>6}")
                lines.append("─" * 40)
                total = 0
                for i in range(len(wps)-1):
                    ax, ay, al, _ = wps[i]
                    bx, by, bl, _ = wps[i+1]
                    h, d = leg_info(ax, ay, bx, by)
                    total += d
                    tag = f"{i}→{i+1}"
                    lines.append(f"{tag:<4} {al[:8]+'→'+bl[:8]:<22}  {h:>6.1f}°  {d:>5}mm")
                lines.append("─" * 40)
                lines.append(f"{'Total':>34}  {total:>5}mm")

        self.txt.config(state=tk.NORMAL)
        self.txt.delete("1.0", tk.END)
        self.txt.insert(tk.END, "\n".join(lines))
        self.txt.config(state=tk.DISABLED)

    # ── Acciones ──────────────────────────────────────────────────────────

    def _remove_last(self):
        if self.waypoints:
            self.waypoints.pop()
            self._redraw()

    def _clear_route(self):
        self.waypoints.clear()
        self._redraw()

    def _clear_zones(self):
        self.user_zones.clear()
        self._redraw()

    def _export(self):
        wps = self.waypoints
        if not wps:
            messagebox.showinfo("Sin datos", "Agrega waypoints primero.")
            return

        lines = [
            "# ══ Código exportado del Simulador WRO 2026 ══",
            "# Pega el bloque goto() en wro_secuencia2.py",
            "",
            "# Posiciones (X mm, Y mm)",
        ]
        for i, (x, y, lbl, typ) in enumerate(wps):
            safe = lbl.upper().replace(" ", "_").replace(".", "")
            lines.append(f"WP{i:02d} = ({x}, {y})  # [{typ}] {lbl}")

        lines += ["", "# ── Secuencia de movimiento ──",
                  "# (pega dentro de run() en wro_secuencia2.py)", ""]
        for i, (x, y, lbl, typ) in enumerate(wps):
            if i == 0:
                lines.append(f"# START: robot en ({x}, {y}) — heading IMU = 0°")
                lines.append(f"self.pos_x, self.pos_y = {x}, {y}")
            else:
                h, d = leg_info(*wps[i-1][:2], x, y)
                comment = f"[{typ}] {lbl} — {d}mm / {h}°"
                lines.append(f"self.goto(({x}, {y}))  # {comment}")
                if typ == "destino":
                    lines.append("self.garra_frontal_agarrar()  # TODO: o _soltar()")

        # Zonas definidas por usuario
        if self.user_zones:
            lines += ["", "# ── Zonas definidas por usuario ──"]
            for (lbl, x1, y1, x2, y2, *_) in self.user_zones:
                cx, cy = (x1+x2)//2, (y1+y2)//2
                safe = lbl.upper().replace(" ", "_").replace("/", "_")
                lines.append(f"ZONA_{safe:<20} = ({cx}, {cy})  # {lbl} [{x1},{y1}→{x2},{y2}]")

        code = "\n".join(lines)
        win = tk.Toplevel(self)
        win.title("Código exportado")
        txt = scrolledtext.ScrolledText(win, font=("Courier", 10), width=68, height=32)
        txt.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        txt.insert(tk.END, code)


# ════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = Simulador()
    app.mainloop()
