"""
wro_gui.py  —  WRO 2026 Mosaic Masters
=======================================
pip install bleak openpyxl
pip install winrt-Windows.Devices.Bluetooth.Advertisement
pip install winrt-Windows.Storage.Streams
"""

import asyncio, math, struct, threading, time
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import deque

import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from bleak import BleakScanner

# ════════════════════════════════════════════════════════════════
#  PROTOCOLO PYBRICKS
# ════════════════════════════════════════════════════════════════
PYBRICKS_MFR_ID = 0x0397
TX_CHANNEL = 1
RX_CHANNEL = 0
TYPE_INT   = 3
TURN_RATE  = 200   # deg/s giro
MOTOR_SPD  = 300   # deg/s motores extra

def _enc(v: int) -> bytes:
    if -128 <= v <= 127:
        return bytes([(TYPE_INT << 5) | 1]) + struct.pack("b", v)
    elif -32768 <= v <= 32767:
        return bytes([(TYPE_INT << 5) | 2]) + struct.pack("<h", v)
    else:
        return bytes([(TYPE_INT << 5) | 4]) + struct.pack("<i", v)

def encode_cmd(speed: int, turn: int, motor_cmd: int = 0, motor_val: int = 0) -> bytes:
    """Empaqueta (speed, turn, motor_cmd, motor_val) en formato Pybricks."""
    return (bytes([TX_CHANNEL])
            + _enc(speed) + _enc(turn)
            + _enc(motor_cmd) + _enc(motor_val))

def decode_color(data: bytes):
    if not data or data[0] != RX_CHANNEL:
        return None
    i = 1
    while i < len(data):
        header = data[i]; i += 1
        vt = (header >> 5) & 0x07
        vl =  header & 0x1F
        if vt == 3:
            if i + vl > len(data): break
            raw = data[i:i+vl]
            v = (struct.unpack("b", raw)[0] if vl == 1
                 else struct.unpack("<h", raw)[0] if vl == 2
                 else struct.unpack("<i", raw)[0])
            return int(v)
        else:
            i += vl
    return None

# ════════════════════════════════════════════════════════════════
#  BLE PUBLISHER  — hilo dedicado, latencia ~50ms
# ════════════════════════════════════════════════════════════════
class BLEPublisher:
    INTERVAL = 0.05

    def __init__(self):
        self._speed     = 0
        self._turn      = 0
        self._motor_cmd = 0
        self._motor_val = 0
        self._stop_evt  = threading.Event()
        self._thread    = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _ibuf(self, data: bytes):
        from winrt.windows.storage.streams import DataWriter
        w = DataWriter()
        for b in data: w.write_byte(b)
        return w.detach_buffer()

    def _make_pub(self, speed, turn, mc, mv):
        from winrt.windows.devices.bluetooth.advertisement import (
            BluetoothLEAdvertisementPublisher,
            BluetoothLEAdvertisement,
            BluetoothLEManufacturerData,
        )
        mfr = BluetoothLEManufacturerData()
        mfr.company_id = PYBRICKS_MFR_ID
        mfr.data = self._ibuf(encode_cmd(speed, turn, mc, mv))
        adv = BluetoothLEAdvertisement()
        adv.manufacturer_data.append(mfr)
        pub = BluetoothLEAdvertisementPublisher(adv)
        pub.start()
        return pub

    def _loop(self):
        pub = None
        cur = (None, None, None, None)
        while not self._stop_evt.is_set():
            nxt = (self._speed, self._turn, self._motor_cmd, self._motor_val)
            if nxt != cur or pub is None:
                if pub:
                    try: pub.stop()
                    except: pass
                try:
                    pub = self._make_pub(*nxt)
                    cur = nxt
                except Exception as e:
                    print(f"[BLE TX] {e}"); pub = None
            else:
                if pub:
                    try: pub.stop()
                    except: pass
                try:
                    pub = self._make_pub(*nxt)
                except Exception as e:
                    print(f"[BLE TX refresh] {e}"); pub = None
            time.sleep(self.INTERVAL)
        if pub:
            try: pub.stop()
            except: pass

    def send(self, speed: int, turn: int, motor_cmd: int = 0, motor_val: int = 0):
        self._speed     = speed
        self._turn      = turn
        self._motor_cmd = motor_cmd
        self._motor_val = motor_val

    def stop(self):
        self._stop_evt.set()

# ════════════════════════════════════════════════════════════════
#  DEAD RECKONING
# ════════════════════════════════════════════════════════════════
class DeadReckoning:
    DT = 0.1  # 100ms loop

    def __init__(self):
        self.x = 0.0; self.y = 0.0; self.heading = 0.0

    def reset(self, x=0.0, y=0.0, heading=0.0):
        self.x = x; self.y = y; self.heading = heading

    def update(self, speed: float, turn: float):
        self.heading = (self.heading + turn * self.DT) % 360
        rad = math.radians(self.heading)
        dist = speed * self.DT
        self.x += dist * math.sin(rad)
        self.y += dist * math.cos(rad)

    @property
    def pos(self): return (self.x, self.y)

# ════════════════════════════════════════════════════════════════
#  COLORES WRO 2026
# ════════════════════════════════════════════════════════════════
COLORS = {
    0: {"name": "Suelo",    "tk": "#333333", "xlsx": "333333", "r": 3},
    1: {"name": "Amarillo", "tk": "#FFD700", "xlsx": "FFD700", "r": 10},
    2: {"name": "Azul",     "tk": "#1E90FF", "xlsx": "1E90FF", "r": 10},
    3: {"name": "Verde",    "tk": "#32CD32", "xlsx": "32CD32", "r": 10},
    4: {"name": "Blanco",   "tk": "#CCCCCC", "xlsx": "CCCCCC", "r": 10},
    5: {"name": "Rojo",     "tk": "#FF4444", "xlsx": "FF4444", "r": 8},
}
FIELD_W = 1200.0
FIELD_H =  900.0

# ════════════════════════════════════════════════════════════════
#  RUTA ÓPTIMA
# ════════════════════════════════════════════════════════════════
def calc_route(points):
    groups = {}
    for p in points:
        if p["c"] != 0: groups.setdefault(p["c"], []).append(p)
    route = []
    for c in [1, 3, 2, 4, 5]:
        grp = list(groups.get(c, []))
        if not grp: continue
        cur = grp.pop(0); route.append(cur)
        while grp:
            nxt = min(grp, key=lambda p: math.hypot(p["x"]-cur["x"], p["y"]-cur["y"]))
            grp.remove(nxt); cur = nxt; route.append(cur)
    return route

# ════════════════════════════════════════════════════════════════
#  EXPORTAR XLSX
# ════════════════════════════════════════════════════════════════
def export_xlsx(points, route, path):
    wb   = openpyxl.Workbook()
    thin = Side(style="thin", color="888888")
    brd  = Border(left=thin, right=thin, top=thin, bottom=thin)

    def H(ws, r, c, v):
        cell = ws.cell(row=r, column=c, value=v)
        cell.font = Font(bold=True, name="Arial", color="FFFFFF", size=10)
        cell.fill = PatternFill("solid", start_color="0F3460")
        cell.alignment = Alignment(horizontal="center"); cell.border = brd

    def D(ws, r, c, v):
        cell = ws.cell(row=r, column=c, value=v)
        cell.alignment = Alignment(horizontal="center")
        cell.border = brd; cell.font = Font(name="Arial", size=10)

    def CC(ws, r, c, ci, v):
        cell = ws.cell(row=r, column=c, value=v)
        cell.fill = PatternFill("solid", start_color=COLORS[ci]["xlsx"])
        txt = "000000" if ci in (1, 4, 0) else "FFFFFF"
        cell.font = Font(name="Arial", color=txt, size=10)
        cell.alignment = Alignment(horizontal="center"); cell.border = brd

    ws1 = wb.active; ws1.title = "Mapa Raw"
    for c, h in enumerate(["#","X (mm)","Y (mm)","Color","Codigo"], 1): H(ws1,1,c,h)
    for i, p in enumerate(points, 1):
        ci = p["c"]
        D(ws1,i+1,1,i); D(ws1,i+1,2,round(p["x"])); D(ws1,i+1,3,round(p["y"]))
        CC(ws1,i+1,4,ci,COLORS[ci]["name"]); D(ws1,i+1,5,ci)
    for w, c in zip([5,12,12,14,10], range(1,6)):
        ws1.column_dimensions[openpyxl.utils.get_column_letter(c)].width = w

    ws2 = wb.create_sheet("Ruta Optima")
    for c, h in enumerate(["Paso","X (mm)","Y (mm)","Color","Dist (mm)","Acum (mm)"], 1): H(ws2,1,c,h)
    prev = None; acum = 0
    for step, p in enumerate(route, 1):
        ci = p["c"]
        dist = round(math.hypot(p["x"]-prev["x"], p["y"]-prev["y"])) if prev else 0
        acum += dist
        D(ws2,step+1,1,step); D(ws2,step+1,2,round(p["x"])); D(ws2,step+1,3,round(p["y"]))
        CC(ws2,step+1,4,ci,COLORS[ci]["name"]); D(ws2,step+1,5,dist); D(ws2,step+1,6,acum)
        prev = p
    t = len(route)+2
    ws2.cell(row=t,column=5,value="TOTAL").font = Font(bold=True,name="Arial")
    ws2.cell(row=t,column=6,value=acum).font    = Font(bold=True,name="Arial")
    for w, c in zip([5,12,12,16,14,14], range(1,7)):
        ws2.column_dimensions[openpyxl.utils.get_column_letter(c)].width = w

    ws3 = wb.create_sheet("Mapa Visual")
    ws3.merge_cells("A1:L1")
    tc = ws3["A1"]
    tc.value = "Mapa Visual WRO 2026  ·  cada celda = 10 cm"
    tc.font  = Font(bold=True, name="Arial", size=12, color="FFFFFF")
    tc.fill  = PatternFill("solid", start_color="1A1A2E")
    tc.alignment = Alignment(horizontal="center")
    ws3.row_dimensions[1].height = 26
    GW, GH = 12, 9
    for row in range(GH):
        for col in range(GW):
            xc = col*100+50; yc = (GH-1-row)*100+50
            best = None; best_d = 70
            for p in points:
                if p["c"] == 0: continue
                d = math.hypot(p["x"]-xc, p["y"]-yc)
                if d < best_d: best_d = d; best = p
            cell = ws3.cell(row=row+3, column=col+1)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = brd
            if best:
                ci = best["c"]
                cell.fill  = PatternFill("solid", start_color=COLORS[ci]["xlsx"])
                cell.value = COLORS[ci]["name"][:3].upper()
                txt = "000000" if ci in (1, 4) else "FFFFFF"
                cell.font  = Font(name="Arial", size=8, color=txt, bold=True)
            else:
                cell.fill = PatternFill("solid", start_color="EEEEEE")
        ws3.row_dimensions[row+3].height = 26
    for col in range(1, GW+1):
        ws3.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 9

    wb.save(path); return acum

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
ORG  = "#FF6600"
PRP  = "#BB86FC"

# ════════════════════════════════════════════════════════════════
#  APP
# ════════════════════════════════════════════════════════════════
class WROApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WRO 2026 — Control + Mapa")
        self.root.configure(bg=BG)
        self.root.geometry("1200x700")
        self.root.minsize(950, 600)

        self._pub  = BLEPublisher()
        self._dr   = DeadReckoning()
        self._points: list[dict] = []
        self._route:  list[dict] = []
        self._trail   = deque(maxlen=1000)
        self._lock    = threading.Lock()

        # Drive
        self._keys    = set()
        self._btn     = None
        self._last_cmd = (0, 0, 0, 0)
        self.spd      = tk.IntVar(value=300)

        # Motor extra activo
        self._motor_held = 0   # 0=none 1=garra_principal 2=agarrar 3=expandir
        self._motor_dir  = 0   # +1 o -1

        self._last_color = 0

        self._build()
        self._bind_keys()
        self._start_ble_rx()
        self._cmd_loop()

    # ─────────────────────────────────────────────────────────────────────────
    def _build(self):
        # ── Toolbar ──────────────────────────────────────────────────────────
        tb = tk.Frame(self.root, bg="#111")
        tb.pack(fill="x")
        tk.Label(tb, text="WRO 2026 — Mosaic Masters",
                 bg="#111", fg=TEXT, font=("Helvetica",12,"bold")).pack(side="left",padx=12,pady=7)
        self.ble_lbl = tk.Label(tb, text="● Sin señal", bg="#111", fg=DIM,
                                font=("Helvetica",10))
        self.ble_lbl.pack(side="right", padx=12)
        self.color_lbl = tk.Label(tb, text="Color: —", bg="#111", fg=DIM,
                                  font=("Helvetica",10,"bold"))
        self.color_lbl.pack(side="right", padx=12)
        tk.Frame(self.root, bg="#252525", height=1).pack(fill="x")

        # ── Body ─────────────────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)

        # ── MAPA ─────────────────────────────────────────────────────────────
        mf = tk.Frame(body, bg=BG)
        mf.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        mhdr = tk.Frame(mf, bg=BG)
        mhdr.pack(fill="x", pady=(0,4))
        tk.Label(mhdr, text="MAPA EN VIVO", bg=BG, fg=DIM,
                 font=("Helvetica",8,"bold")).pack(side="left")
        self.pos_lbl = tk.Label(mhdr, text="X=0  Y=0  Hdg=0°",
                                bg=BG, fg=CYAN, font=("Courier",9))
        self.pos_lbl.pack(side="right")

        self.cv = tk.Canvas(mf, bg="#111", highlightthickness=1,
                            highlightbackground="#333")
        self.cv.pack(fill="both", expand=True)
        self.cv.bind("<Configure>",  lambda e: self._redraw())
        self.cv.bind("<Button-1>",   self._click_set_pos)
        self.cv.bind("<Button-3>",   self._click_add_point)

        tk.Label(mf, text="Click izq = reubicar robot   |   Click der = añadir punto manual",
                 bg=BG, fg=DIM, font=("Helvetica",7)).pack(anchor="w")

        # ── PANEL DERECHO ─────────────────────────────────────────────────────
        pf = tk.Frame(body, bg=BG, width=280)
        pf.pack(side="right", fill="y", padx=(0,10), pady=10)
        pf.pack_propagate(False)

        c2 = tk.Canvas(pf, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(pf, orient="vertical", command=c2.yview)
        c2.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        c2.pack(side="left", fill="both", expand=True)
        inn = tk.Frame(c2, bg=BG, width=260)
        c2.create_window((0,0), window=inn, anchor="nw", width=260)
        inn.bind("<Configure>", lambda e: c2.configure(scrollregion=c2.bbox("all")))

        def sep():
            tk.Frame(inn, bg="#252525", height=1).pack(fill="x", pady=7)

        def lbl(t):
            tk.Label(inn, text=t, bg=BG, fg=DIM,
                     font=("Helvetica",8,"bold")).pack(anchor="w", pady=(0,4))

        # ── D-PAD ─────────────────────────────────────────────────────────────
        lbl("CONTROL RUEDAS  (WASD / flechas)")
        pad = tk.Frame(inn, bg=BG); pad.pack()
        bkw = dict(width=4,height=2,relief="flat",cursor="hand2",
                   font=("Helvetica",20),bg=CARD,fg=TEXT,
                   activebackground="#1E3A4A",activeforeground=CYAN)

        tk.Label(pad,bg=BG,width=4,height=2).grid(row=0,column=0,padx=3,pady=2)
        self.b_fwd=tk.Button(pad,text="▲",**bkw)
        self.b_fwd.grid(row=0,column=1,padx=3,pady=2)
        tk.Label(pad,bg=BG,width=4,height=2).grid(row=0,column=2,padx=3,pady=2)

        self.b_left=tk.Button(pad,text="◀",**bkw)
        self.b_left.grid(row=1,column=0,padx=3,pady=2)
        self.b_stop=tk.Button(pad,text="⏹",width=4,height=2,relief="flat",
                              cursor="hand2",font=("Helvetica",20),
                              bg="#1E1E1E",fg=RED,
                              activebackground="#2A2A2A",activeforeground=RED)
        self.b_stop.grid(row=1,column=1,padx=3,pady=2)
        self.b_right=tk.Button(pad,text="▶",**bkw)
        self.b_right.grid(row=1,column=2,padx=3,pady=2)

        tk.Label(pad,bg=BG,width=4,height=2).grid(row=2,column=0,padx=3,pady=2)
        self.b_back=tk.Button(pad,text="▼",**bkw)
        self.b_back.grid(row=2,column=1,padx=3,pady=2)
        tk.Label(pad,bg=BG,width=4,height=2).grid(row=2,column=2,padx=3,pady=2)

        for btn, act in [(self.b_fwd,"fwd"),(self.b_back,"back"),
                         (self.b_left,"left"),(self.b_right,"right")]:
            btn.bind("<ButtonPress-1>",   lambda e,a=act: self._bp(a))
            btn.bind("<ButtonRelease-1>", lambda e: self._br())
        self.b_stop.bind("<ButtonPress-1>", lambda e: self._estop())

        # Velocidad ruedas
        sf = tk.Frame(inn,bg=BG); sf.pack(fill="x",pady=4)
        tk.Label(sf,text="Vel ruedas:",bg=BG,fg=DIM,font=("Helvetica",9)).pack(side="left")
        tk.Scale(sf,variable=self.spd,from_=50,to=600,orient="horizontal",
                 bg=BG,fg=TEXT,troughcolor="#2A2A2A",highlightthickness=0,
                 sliderrelief="flat",activebackground=CYAN,length=145).pack(side="right")

        self.cmd_lbl = tk.Label(inn,text="spd=0  trn=0",bg=BG,fg=DIM,font=("Courier",8))
        self.cmd_lbl.pack()

        sep()

        # ── MOTORES EXTRA ─────────────────────────────────────────────────────
        lbl("MOTORES EXTRA  (mantén presionado)")

        motor_cfg = [
            (1, "Garra Principal",  "A", PRP),
            (2, "Agarrar Bloques",  "E", "#FF9500"),
            (3, "Expandir Garra",   "C", "#00E5CC"),
        ]

        for motor_id, name, port, color in motor_cfg:
            mrow = tk.Frame(inn, bg=BG); mrow.pack(fill="x", pady=3)
            tk.Label(mrow, text=f"{name} ({port})", bg=BG, fg=TEXT,
                     font=("Helvetica",9)).pack(side="left")

            btn_frame = tk.Frame(mrow, bg=BG)
            btn_frame.pack(side="right")

            mkw = dict(width=3, height=1, relief="flat", cursor="hand2",
                       font=("Helvetica",12), bg=CARD, fg=color,
                       activebackground="#2A2A2A", activeforeground=color)

            b_minus = tk.Button(btn_frame, text="−", **mkw)
            b_minus.pack(side="left", padx=2)
            b_plus  = tk.Button(btn_frame, text="+", **mkw)
            b_plus.pack(side="left", padx=2)

            b_minus.bind("<ButtonPress-1>",
                         lambda e, mid=motor_id: self._motor_press(mid, -1))
            b_minus.bind("<ButtonRelease-1>",
                         lambda e: self._motor_release())
            b_plus.bind("<ButtonPress-1>",
                        lambda e, mid=motor_id: self._motor_press(mid, +1))
            b_plus.bind("<ButtonRelease-1>",
                        lambda e: self._motor_release())

        self.motor_lbl = tk.Label(inn, text="Motor: —", bg=BG, fg=DIM,
                                  font=("Courier",8))
        self.motor_lbl.pack(pady=(4,0))

        sep()

        # ── POSICIÓN ──────────────────────────────────────────────────────────
        lbl("POSICIÓN ESTIMADA")
        pos_card = tk.Frame(inn,bg=CARD); pos_card.pack(fill="x",pady=(0,4))
        self.pos_card_lbl = tk.Label(pos_card,
            text="X=0 mm\nY=0 mm\nHeading=0°",
            bg=CARD,fg=CYAN,font=("Courier",10),justify="left")
        self.pos_card_lbl.pack(padx=10,pady=8,anchor="w")

        tk.Button(inn,text="📍  Resetear posición a (0,0)",bg=CARD,fg=AMB,
                  relief="flat",cursor="hand2",font=("Helvetica",9),pady=5,
                  command=self._reset_pos).pack(fill="x",pady=2)

        sep()

        # ── STATS ─────────────────────────────────────────────────────────────
        lbl("DETECCIONES")
        self._sl={}
        sf2=tk.Frame(inn,bg=CARD); sf2.pack(fill="x",pady=(0,4))
        for key,label,col in [
            ("pts","Total",CYAN),
            ("yel","Amarillo","#FFD700"),("blu","Azul","#1E90FF"),
            ("grn","Verde","#32CD32"),("wht","Blanco","#CCCCCC"),
            ("red","Rojo","#FF4444"),
        ]:
            row=tk.Frame(sf2,bg=CARD); row.pack(fill="x",padx=8,pady=1)
            tk.Label(row,text=label+":",bg=CARD,fg=DIM,font=("Helvetica",9)).pack(side="left")
            l=tk.Label(row,text="0",bg=CARD,fg=col,font=("Courier",9,"bold"))
            l.pack(side="right"); self._sl[key]=l

        sep()

        # ── ACCIONES ─────────────────────────────────────────────────────────
        lbl("ACCIONES MAPA")
        bm = dict(relief="flat",cursor="hand2",font=("Helvetica",10),pady=7)
        tk.Button(inn,text="⟳  Limpiar mapa",bg=CARD,fg=TEXT,
                  activebackground="#2A2A2A",**bm,command=self._clear).pack(fill="x",pady=2)
        tk.Button(inn,text="📍  Calcular ruta óptima",bg="#0F3460",fg=CYAN,
                  activebackground="#1A4A80",**bm,command=self._route_btn).pack(fill="x",pady=2)
        self.route_lbl=tk.Label(inn,text="",bg=BG,fg=GRN,
                                font=("Helvetica",8),wraplength=250)
        self.route_lbl.pack(pady=(0,4))
        tk.Button(inn,text="💾  Exportar XLSX",bg="#1A3A1A",fg=GRN,
                  activebackground="#2A4A2A",**bm,command=self._export).pack(fill="x",pady=2)

        sep()

        # ── LEYENDA ───────────────────────────────────────────────────────────
        lbl("LEYENDA COLORES")
        for ci,info in COLORS.items():
            if ci==0: continue
            row=tk.Frame(inn,bg=BG); row.pack(fill="x",pady=1)
            dot=tk.Canvas(row,bg=BG,width=14,height=14,highlightthickness=0)
            dot.pack(side="left")
            dot.create_oval(2,2,12,12,fill=info["tk"],outline="")
            tk.Label(row,text=info["name"],bg=BG,fg=TEXT,
                     font=("Helvetica",9)).pack(side="left",padx=4)

    # ─────────────────────────────────────────────────────────────────────────
    #  TECLADO
    # ─────────────────────────────────────────────────────────────────────────
    def _bind_keys(self):
        self.root.bind("<KeyPress>",   lambda e: self._keys.add(e.keysym.lower()))
        self.root.bind("<KeyRelease>", lambda e: self._keys.discard(e.keysym.lower()))
        self.root.focus_set()

    # ─────────────────────────────────────────────────────────────────────────
    #  BOTONES D-PAD
    # ─────────────────────────────────────────────────────────────────────────
    def _bp(self, a):
        self._btn = a
        m={"fwd":self.b_fwd,"back":self.b_back,"left":self.b_left,"right":self.b_right}
        b=m.get(a)
        if b: b.config(bg="#1E3A4A",fg=CYAN)

    def _br(self):
        m={"fwd":self.b_fwd,"back":self.b_back,"left":self.b_left,"right":self.b_right}
        b=m.get(self._btn)
        if b: b.config(bg=CARD,fg=TEXT)
        self._btn=None

    def _estop(self):
        self._btn=None; self._keys.clear()
        self._motor_held=0; self._motor_dir=0
        self._send(0,0,0,0)

    # ─────────────────────────────────────────────────────────────────────────
    #  BOTONES MOTORES EXTRA
    # ─────────────────────────────────────────────────────────────────────────
    def _motor_press(self, motor_id: int, direction: int):
        self._motor_held = motor_id
        self._motor_dir  = direction
        names = {1:"Garra Principal",2:"Agarrar Bloques",3:"Expandir Garra"}
        sign  = "+" if direction > 0 else "−"
        self.motor_lbl.config(
            text=f"Motor: {names.get(motor_id,'?')} {sign}{MOTOR_SPD}°/s",
            fg=PRP)

    def _motor_release(self):
        self._motor_held = 0
        self._motor_dir  = 0
        self.motor_lbl.config(text="Motor: —", fg=DIM)

    # ─────────────────────────────────────────────────────────────────────────
    #  LOOP DE CONTROL + DEAD RECKONING (100ms)
    # ─────────────────────────────────────────────────────────────────────────
    def _cmd_loop(self):
        spd, trn = self._compute_drive()
        mc  = self._motor_held
        mv  = MOTOR_SPD * self._motor_dir if mc != 0 else 0

        cmd = (spd, trn, mc, mv)
        if cmd != self._last_cmd:
            self._send(*cmd)
            self._last_cmd = cmd

        # Dead reckoning
        self._dr.update(spd, trn)
        self._trail.append(self._dr.pos)

        # Registrar punto de color si el robot se mueve
        if self._last_color != 0 and (spd != 0 or trn != 0):
            x, y = self._dr.pos
            with self._lock:
                dup = any(
                    math.hypot(p["x"]-x, p["y"]-y) < 30 and p["c"] == self._last_color
                    for p in self._points)
                if not dup:
                    self._points.append({"x":x,"y":y,"c":self._last_color})
            self._update_stats()

        self._update_pos_labels()
        self._redraw()
        self.root.after(100, self._cmd_loop)

    def _compute_drive(self):
        s=self.spd.get(); k=self._keys; b=self._btn
        fwd  ="w" in k or "up"    in k or b=="fwd"
        back ="s" in k or "down"  in k or b=="back"
        left ="a" in k or "left"  in k or b=="left"
        right="d" in k or "right" in k or b=="right"
        spd = s if fwd else (-s if back else 0)
        trn = TURN_RATE if right else (-TURN_RATE if left else 0)
        return spd, trn

    def _send(self, spd, trn, mc=0, mv=0):
        self._pub.send(spd, trn, mc, mv)
        moving = spd!=0 or trn!=0 or mc!=0
        self.ble_lbl.config(
            text=f"● {'Activo' if moving else 'Conectado ✓'}",
            fg=GRN if moving else CYAN)
        self.cmd_lbl.config(text=f"spd={spd:+4d}  trn={trn:+4d}")

    def _update_pos_labels(self):
        x,y = self._dr.pos
        h   = round(self._dr.heading,1)
        self.pos_card_lbl.config(
            text=f"X={round(x)} mm\nY={round(y)} mm\nHeading={h}°")
        self.pos_lbl.config(text=f"X={round(x)}  Y={round(y)}  Hdg={h}°")

    # ─────────────────────────────────────────────────────────────────────────
    #  BLE RX
    # ─────────────────────────────────────────────────────────────────────────
    def _start_ble_rx(self):
        threading.Thread(target=lambda: asyncio.run(self._scan()), daemon=True).start()

    async def _scan(self):
        def on_adv(device, adv):
            mfr = adv.manufacturer_data
            if PYBRICKS_MFR_ID not in mfr: return
            c = decode_color(mfr[PYBRICKS_MFR_ID])
            if c is None: return
            self._last_color = c
            info = COLORS.get(c, COLORS[0])
            self.root.after(0, self._update_color_label, c, info)

        try:
            sc = BleakScanner(detection_callback=on_adv, scanning_mode="passive")
        except Exception:
            sc = BleakScanner(detection_callback=on_adv)
        async with sc:
            while True:
                await asyncio.sleep(1)

    def _update_color_label(self, c, info):
        self.color_lbl.config(
            text=f"Color: {info['name']}",
            fg=info["tk"] if c!=0 else DIM)

    def _update_stats(self):
        with self._lock: pts=list(self._points)
        counts={c:sum(1 for p in pts if p["c"]==c) for c in [1,2,3,4,5]}
        self._sl["pts"].config(text=str(len(pts)))
        self._sl["yel"].config(text=str(counts[1]))
        self._sl["blu"].config(text=str(counts[2]))
        self._sl["grn"].config(text=str(counts[3]))
        self._sl["wht"].config(text=str(counts[4]))
        self._sl["red"].config(text=str(counts[5]))

    # ─────────────────────────────────────────────────────────────────────────
    #  CANVAS
    # ─────────────────────────────────────────────────────────────────────────
    def _px(self, x_mm, y_mm):
        w = self.cv.winfo_width()  or 600
        h = self.cv.winfo_height() or 450
        return int(x_mm/FIELD_W*w), int((1-y_mm/FIELD_H)*h)

    def _px_to_mm(self, px, py):
        w = self.cv.winfo_width()  or 600
        h = self.cv.winfo_height() or 450
        return px/w*FIELD_W, (1-py/h)*FIELD_H

    def _draw_robot(self, cv, rx, ry, heading_deg):
        """
        Dibuja el robot como un triángulo que apunta en la dirección
        real del heading. heading=0 → apunta arriba (+Y en el mapa).
        """
        size = 12
        # heading=0 → apunta en +Y (arriba en pantalla = ángulo -90° en canvas)
        # Convertimos: ángulo_canvas = -(heading - 90) para que 0° = arriba
        angle = math.radians(heading_deg)   # mismo sistema que dead reckoning

        # Punta del triángulo (frente del robot)
        tip_x = rx + size * math.sin(angle)
        tip_y = ry - size * math.cos(angle)

        # Esquinas traseras
        back_angle_l = angle + math.radians(140)
        back_angle_r = angle - math.radians(140)
        bl_x = rx + size * 0.7 * math.sin(back_angle_l)
        bl_y = ry - size * 0.7 * math.cos(back_angle_l)
        br_x = rx + size * 0.7 * math.sin(back_angle_r)
        br_y = ry - size * 0.7 * math.cos(back_angle_r)

        cv.create_polygon(
            tip_x, tip_y,
            bl_x,  bl_y,
            br_x,  br_y,
            fill=AMB, outline="#FFFFFF", width=2)

        # Punto central
        cv.create_oval(rx-3,ry-3,rx+3,ry+3, fill="#FFFFFF", outline="")

    def _redraw(self):
        cv = self.cv; cv.delete("all")
        w = cv.winfo_width() or 600
        h = cv.winfo_height() or 450

        # Grid
        for gx in range(0, int(FIELD_W)+1, 100):
            px = int(gx/FIELD_W*w)
            cv.create_line(px,0,px,h, fill="#1C1C1C")
            if gx > 0:
                cv.create_text(px+2,h-2,anchor="se",
                               text=f"{gx//10}",fill="#2A2A2A",font=("Helvetica",6))
        for gy in range(0, int(FIELD_H)+1, 100):
            py = int((1-gy/FIELD_H)*h)
            cv.create_line(0,py,w,py, fill="#1C1C1C")
            if gy > 0:
                cv.create_text(3,py-2,anchor="sw",
                               text=f"{gy//10}",fill="#2A2A2A",font=("Helvetica",6))
        cv.create_rectangle(1,1,w-1,h-1, outline="#444", width=2)

        # Origen (0,0)
        ox,oy = self._px(0,0)
        cv.create_line(ox-12,oy,ox+12,oy, fill=ORG, width=2)
        cv.create_line(ox,oy-12,ox,oy+12, fill=ORG, width=2)
        cv.create_text(ox+14,oy-8, text="(0,0)", fill=ORG, font=("Helvetica",7,"bold"))

        # Trail
        trail = list(self._trail)
        for i in range(1, len(trail)):
            x1,y1=self._px(*trail[i-1]); x2,y2=self._px(*trail[i])
            cv.create_line(x1,y1,x2,y2, fill="#1E5555", width=1)

        # Ruta óptima
        if self._route:
            for i in range(1, len(self._route)):
                p1=self._route[i-1]; p2=self._route[i]
                x1,y1=self._px(p1["x"],p1["y"]); x2,y2=self._px(p2["x"],p2["y"])
                cv.create_line(x1,y1,x2,y2, fill=CYAN, width=2, dash=(5,3))
            for step, p in enumerate(self._route, 1):
                px,py=self._px(p["x"],p["y"])
                cv.create_oval(px-4,py-4,px+4,py+4, fill=CYAN, outline="")
                cv.create_text(px+10,py-10, text=str(step),
                               fill=CYAN, font=("Helvetica",7,"bold"))

        # Puntos detectados
        with self._lock: pts=list(self._points)
        for p in pts:
            ci=p["c"]; r=COLORS[ci]["r"]
            px,py=self._px(p["x"],p["y"])
            cv.create_oval(px-r,py-r,px+r,py+r,
                           fill=COLORS[ci]["tk"],outline="#FFF",width=1)
            cv.create_text(px,py, text=COLORS[ci]["name"][0],
                           fill="black", font=("Helvetica",6,"bold"))

        # Robot con triángulo alineado al heading
        rx, ry = self._px(*self._dr.pos)
        self._draw_robot(cv, rx, ry, self._dr.heading)

    # ─────────────────────────────────────────────────────────────────────────
    #  CLICKS EN EL CANVAS
    # ─────────────────────────────────────────────────────────────────────────
    def _click_set_pos(self, event):
        x_mm, y_mm = self._px_to_mm(event.x, event.y)
        x_mm = max(0, min(FIELD_W, x_mm))
        y_mm = max(0, min(FIELD_H, y_mm))
        self._dr.reset(x_mm, y_mm, self._dr.heading)
        self._trail.clear()
        self._trail.append((x_mm, y_mm))

    def _click_add_point(self, event):
        x_mm, y_mm = self._px_to_mm(event.x, event.y)
        popup = tk.Menu(self.root, tearoff=0, bg=CARD, fg=TEXT)
        for ci, info in COLORS.items():
            if ci == 0: continue
            popup.add_command(
                label=f"  {info['name']}",
                command=lambda x=x_mm,y=y_mm,c=ci: self._add_pt(x,y,c))
        popup.tk_popup(event.x_root, event.y_root)

    def _add_pt(self, x, y, c):
        with self._lock:
            self._points.append({"x":x,"y":y,"c":c})
        self._update_stats(); self._redraw()

    # ─────────────────────────────────────────────────────────────────────────
    #  ACCIONES
    # ─────────────────────────────────────────────────────────────────────────
    def _reset_pos(self):
        self._dr.reset(0.0, 0.0, 0.0)
        self._trail.clear()

    def _clear(self):
        with self._lock: self._points.clear()
        self._route.clear(); self._trail.clear()
        self.route_lbl.config(text="")
        self._update_stats(); self._redraw()

    def _route_btn(self):
        with self._lock: pts=list(self._points)
        if not pts:
            messagebox.showinfo("Sin datos","Mueve el robot por el campo primero."); return
        self._route=calc_route(pts)
        total=sum(
            math.hypot(self._route[i]["x"]-self._route[i-1]["x"],
                       self._route[i]["y"]-self._route[i-1]["y"])
            for i in range(1,len(self._route)))
        self.route_lbl.config(
            text=f"✓ {len(self._route)} paradas · {round(total/10)} cm")
        self._redraw()

    def _export(self):
        with self._lock: pts=list(self._points)
        if not pts:
            messagebox.showinfo("Sin datos","Mapea el campo primero."); return
        if not self._route: self._route_btn()
        path=filedialog.asksaveasfilename(
            defaultextension=".xlsx",filetypes=[("Excel","*.xlsx")],
            initialfile="wro2026_mapa.xlsx",title="Guardar mapa WRO 2026")
        if not path: return
        try:
            total=export_xlsx(pts,self._route,path)
            messagebox.showinfo("✓ Guardado",
                f"Puntos: {len(pts)}\n"
                f"Paradas: {len(self._route)}\n"
                f"Dist. total: {round(total/10)} cm\n\n{path}")
        except Exception as e:
            messagebox.showerror("Error",str(e))

# ════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════
def main():
    root = tk.Tk()
    app  = WROApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app._pub.stop(), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    main()