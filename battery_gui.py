"""
spike_battery_gui.py
GUI para leer la batería del SPIKE Prime v5 vía BLE (Pybricks).

Requisitos:
    pip install bleak

Cómo usarlo:
    1. Carga spike_battery_broadcast.py en el SPIKE Prime con Pybricks.
    2. Corre ese script en el hub.
    3. Ejecuta este archivo: python spike_battery_gui.py
"""

import asyncio
import struct
import threading
import tkinter as tk
from tkinter import scrolledtext

from bleak import BleakScanner
from bleak.backends.scanner import AdvertisementData

# ── Protocolo Pybricks (spec oficial) ───────────────────────────────────────
# https://github.com/pybricks/technical-info/blob/master/pybricks-ble-broadcast-observe.md
PYBRICKS_MFR_ID = 0x0397   # LEGO Company Identifier
TARGET_CHANNEL  = 0

# Tipos de dato Pybricks
TYPE_SINGLE = 0
TYPE_TRUE   = 1
TYPE_FALSE  = 2
TYPE_INT    = 3
TYPE_FLOAT  = 4
TYPE_STR    = 5
TYPE_BYTES  = 6

# Voltajes de referencia SPIKE Prime recargable (mV)
BATTERY_FULL  = 8350
BATTERY_EMPTY = 6000


def decode_pybricks_payload(data: bytes):
    """
    Decodifica manufacturer data de Pybricks.
    data[0]  = canal
    data[1:] = valores: header_byte=(type<<5|length) seguido de value_bytes
    Retorna lista de valores Python, o None si canal != TARGET_CHANNEL.
    """
    if not data:
        return None
    if data[0] != TARGET_CHANNEL:
        return None

    values = []
    i = 1
    while i < len(data):
        header    = data[i]; i += 1
        val_type  = (header >> 5) & 0x07
        val_len   = header & 0x1F

        if val_type == TYPE_SINGLE:
            continue  # solo marca que el siguiente es un objeto único
        elif val_type == TYPE_TRUE:
            values.append(True)
        elif val_type == TYPE_FALSE:
            values.append(False)
        elif val_type == TYPE_INT:
            if i + val_len > len(data): break
            raw = data[i:i + val_len]
            if val_len == 1:
                v = struct.unpack("b", raw)[0]
            elif val_len == 2:
                v = struct.unpack("<h", raw)[0]
            else:
                v = struct.unpack("<i", raw)[0]
            values.append(v); i += val_len
        elif val_type == TYPE_FLOAT:
            if i + 4 > len(data): break
            v = struct.unpack_from("<f", data, i)[0]
            values.append(v); i += 4
        elif val_type in (TYPE_STR, TYPE_BYTES):
            if i + val_len > len(data): break
            raw = data[i:i + val_len]
            values.append(raw.decode("utf-8", errors="replace") if val_type == TYPE_STR else bytes(raw))
            i += val_len
        else:
            i += val_len  # tipo desconocido, saltar

    return values or None


def voltage_to_pct(mv: int) -> int:
    return max(0, min(100, int((mv - BATTERY_EMPTY) / (BATTERY_FULL - BATTERY_EMPTY) * 100)))


def pct_color(pct: int) -> str:
    return "#00D4FF" if pct > 60 else ("#FFB800" if pct > 30 else "#FF4444")


# ── GUI ───────────────────────────────────────────────────────────────────────
class App:
    BG, CARD, TEXT, MUTED = "#0F0F0F", "#1A1A1A", "#FFFFFF", "#555555"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SPIKE Prime — Battery Monitor")
        self.root.configure(bg=self.BG)
        self.root.resizable(False, False)
        self._bar_pct = 0
        self._debug = tk.BooleanVar(value=False)
        self._build()
        self._start_ble()

    def _build(self):
        P = 20
        # Header
        h = tk.Frame(self.root, bg=self.BG)
        h.pack(fill="x", padx=P, pady=(P, 0))
        tk.Label(h, text="SPIKE Prime v5", bg=self.BG, fg=self.TEXT,
                 font=("Helvetica", 15, "bold")).pack(side="left")
        self.sdot = tk.Label(h, text="●", bg=self.BG, fg=self.MUTED, font=("Helvetica", 13))
        self.sdot.pack(side="right")
        self.slbl = tk.Label(h, text="Buscando...", bg=self.BG, fg=self.MUTED, font=("Helvetica", 10))
        self.slbl.pack(side="right", padx=(0, 4))

        tk.Frame(self.root, bg="#252525", height=1).pack(fill="x", padx=P, pady=10)

        # Battery % card
        c = tk.Frame(self.root, bg=self.CARD)
        c.pack(fill="x", padx=P, pady=(0, 10))
        tk.Label(c, text="NIVEL DE BATERÍA", bg=self.CARD, fg=self.MUTED,
                 font=("Helvetica", 8, "bold")).pack(anchor="w", padx=14, pady=(12, 0))
        self.pct_lbl = tk.Label(c, text="—", bg=self.CARD, fg="#00D4FF",
                                font=("Helvetica", 52, "bold"))
        self.pct_lbl.pack(anchor="w", padx=14)
        self.bar = tk.Canvas(c, bg=self.CARD, height=12, highlightthickness=0)
        self.bar.pack(fill="x", padx=14, pady=(2, 14))
        self.bar.bind("<Configure>", lambda e: self._draw_bar())

        # Stats row
        row = tk.Frame(self.root, bg=self.BG)
        row.pack(fill="x", padx=P, pady=(0, P))
        self.vf = self._stat(row, "VOLTAJE",   "mV", "#00D4FF")
        self.vf.pack(side="left", expand=True, fill="both", padx=(0, 5))
        self.cf = self._stat(row, "CORRIENTE", "mA", "#FFB800")
        self.cf.pack(side="left", expand=True, fill="both", padx=(5, 0))

        # Debug toggle
        ctrl = tk.Frame(self.root, bg=self.BG)
        ctrl.pack(fill="x", padx=P, pady=(0, 4))
        tk.Checkbutton(ctrl, text="Mostrar log BLE (debug)", variable=self._debug,
                       bg=self.BG, fg=self.MUTED, selectcolor=self.BG,
                       activebackground=self.BG, activeforeground=self.MUTED,
                       font=("Helvetica", 9), command=self._toggle_log).pack(side="left")

        # Log box (oculto por defecto)
        self.log_frame = tk.Frame(self.root, bg=self.BG)
        self.log_box = scrolledtext.ScrolledText(
            self.log_frame, height=9, bg="#111", fg="#0F0",
            font=("Courier", 9), state="disabled", relief="flat"
        )
        self.log_box.pack(fill="both", expand=True, padx=P, pady=(0, P))

    def _stat(self, parent, label, unit, color):
        f = tk.Frame(parent, bg=self.CARD)
        tk.Label(f, text=label, bg=self.CARD, fg=self.MUTED,
                 font=("Helvetica", 8, "bold")).pack(anchor="w", padx=12, pady=(10, 0))
        r = tk.Frame(f, bg=self.CARD)
        r.pack(anchor="w", padx=12, pady=(0, 10))
        lbl = tk.Label(r, text="—", bg=self.CARD, fg=color, font=("Helvetica", 26, "bold"))
        lbl.pack(side="left")
        tk.Label(r, text=f" {unit}", bg=self.CARD, fg=self.MUTED,
                 font=("Helvetica", 11)).pack(side="left", anchor="s", pady=3)
        f._val = lbl
        return f

    def _toggle_log(self):
        if self._debug.get():
            self.log_frame.pack(fill="x")
        else:
            self.log_frame.pack_forget()
        self.root.geometry("")

    def _draw_bar(self):
        self.bar.delete("all")
        w, h, r = self.bar.winfo_width(), 12, 6
        self._rr(0, 0, w, h, r, fill="#2A2A2A", outline="")
        fw = max(0, int(w * self._bar_pct / 100))
        if fw:
            self._rr(0, 0, fw, h, r, fill=pct_color(self._bar_pct), outline="")

    def _rr(self, x1, y1, x2, y2, r, **kw):
        c = self.bar
        c.create_arc(x1,    y1,    x1+2*r, y1+2*r, start=90,  extent=90, style="pieslice", **kw)
        c.create_arc(x2-2*r,y1,    x2,     y1+2*r, start=0,   extent=90, style="pieslice", **kw)
        c.create_arc(x2-2*r,y2-2*r,x2,     y2,     start=270, extent=90, style="pieslice", **kw)
        c.create_arc(x1,    y2-2*r,x1+2*r, y2,     start=180, extent=90, style="pieslice", **kw)
        c.create_rectangle(x1+r, y1, x2-r, y2, **kw)
        c.create_rectangle(x1, y1+r, x2, y2-r, **kw)

    # ── Actualizar UI ─────────────────────────────────────────────────────────
    def update_battery(self, mv: int, ma: int):
        pct = voltage_to_pct(mv)
        self._bar_pct = pct
        self.pct_lbl.config(text=f"{pct}%", fg=pct_color(pct))
        self.vf._val.config(text=str(mv))
        self.cf._val.config(text=str(ma))
        self.slbl.config(text="Conectado ✓", fg="#00FF88")
        self.sdot.config(fg="#00FF88")
        self._draw_bar()

    def log(self, msg: str):
        if not self._debug.get():
            return
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    # ── BLE ───────────────────────────────────────────────────────────────────
    def _start_ble(self):
        threading.Thread(target=lambda: asyncio.run(self._scan()), daemon=True).start()

    async def _scan(self):
        self.root.after(0, self.log, "Iniciando escáner BLE...")

        def cb(device, adv: AdvertisementData):
            mfr = adv.manufacturer_data
            if not mfr:
                return

            # Log todos los manufacturer IDs encontrados
            ids = [hex(k) for k in mfr.keys()]
            self.root.after(0, self.log,
                f"[{device.address}] {device.name or 'N/A'} ids={ids}")

            if PYBRICKS_MFR_ID not in mfr:
                return

            raw = mfr[PYBRICKS_MFR_ID]
            self.root.after(0, self.log, f"  Pybricks raw={raw.hex()} canal={raw[0] if raw else '?'}")

            vals = decode_pybricks_payload(raw)
            if vals is None:
                self.root.after(0, self.log, "  → Canal distinto, ignorando")
                return

            self.root.after(0, self.log, f"  → Decodificado: {vals}")
            if len(vals) >= 2:
                self.root.after(0, self.update_battery, int(vals[0]), int(vals[1]))

        # Intentar passive scanning (captura ADV_NONCONN_IND del SPIKE)
        try:
            scanner = BleakScanner(detection_callback=cb, scanning_mode="passive")
            self.root.after(0, self.log, "Modo: passive scan")
        except Exception as e:
            scanner = BleakScanner(detection_callback=cb)
            self.root.after(0, self.log, f"Modo: active scan (passive no soportado: {e})")

        async with scanner:
            self.root.after(0, self.log, "Escaneando... (asegúrate que el hub está corriendo el script)")
            while True:
                await asyncio.sleep(1)


def main():
    root = tk.Tk()
    root.minsize(360, 240)
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()