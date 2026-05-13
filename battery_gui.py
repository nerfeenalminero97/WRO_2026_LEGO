"""
spike_battery_gui.py
GUI para leer la batería del SPIKE Prime v5 vía BLE.

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
from tkinter import font as tkfont

from bleak import BleakScanner

# ── Pybricks BLE Advertisement constants ────────────────────────────────────
# Pybricks usa el Manufacturer ID 0x0397 (Little Endian) en los advertisements.
PYBRICKS_MFR_ID = 0x0397
# El canal 0 es el primer byte del payload tras el header de Pybricks.
TARGET_CHANNEL = 0

# Voltaje nominal de batería AAA / Li-ion LEGO en mV
BATTERY_FULL = 8400    # ~8.4 V (2 celdas Li-ion full)
BATTERY_EMPTY = 6000   # ~6.0 V (límite seguro)


def parse_pybricks_advertisement(mfr_data: bytes):
    """
    Intenta parsear un advertisement de Pybricks y extraer
    (voltage_mV, current_mA) del canal 0.

    Formato Pybricks (simplificado):
        [0]   : tipo de hub (ignorar)
        [1]   : canal
        [2..] : datos (tuple empaquetado como TLV simple)
    """
    if len(mfr_data) < 3:
        return None

    channel = mfr_data[1]
    if channel != TARGET_CHANNEL:
        return None

    payload = mfr_data[2:]

    # Pybricks empaqueta tuples de ints como valores TLV.
    # Cada valor tiene: 1 byte tipo + N bytes dato.
    # Tipo 0x20 = int de 2 bytes (signed int16)
    # Tipo 0x40 = int de 4 bytes (signed int32)
    # Tipo 0x00 = int de 1 byte (signed int8)
    values = []
    i = 0
    while i < len(payload):
        if i >= len(payload):
            break
        type_byte = payload[i]
        i += 1

        if type_byte == 0x00:          # int8
            if i + 1 > len(payload): break
            val = struct.unpack_from("b", payload, i)[0]
            i += 1
            values.append(val)
        elif type_byte == 0x20:        # int16
            if i + 2 > len(payload): break
            val = struct.unpack_from("<h", payload, i)[0]
            i += 2
            values.append(val)
        elif type_byte == 0x40:        # int32
            if i + 4 > len(payload): break
            val = struct.unpack_from("<i", payload, i)[0]
            i += 4
            values.append(val)
        elif type_byte == 0x01:        # float (5 bytes: tipo + 4 data)
            if i + 4 > len(payload): break
            val = struct.unpack_from("<f", payload, i)[0]
            i += 4
            values.append(val)
        else:
            # Tipo desconocido — salir
            break

    if len(values) >= 2:
        return int(values[0]), int(values[1])
    return None


class SpikeBatteryApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SPIKE Prime — Battery Monitor")
        self.root.resizable(False, False)
        self.root.configure(bg="#0F0F0F")

        self._voltage = None
        self._current = None
        self._scanning = False
        self._device_name = "—"

        self._build_ui()
        self._start_ble_loop()

    # ── UI ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        PAD = 24
        BG = "#0F0F0F"
        CARD = "#1A1A1A"
        ACCENT = "#00D4FF"
        TEXT = "#FFFFFF"
        MUTED = "#666666"

        # ── Header ──────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=PAD, pady=(PAD, 0))

        tk.Label(header, text="🔵", bg=BG, font=("Helvetica", 20)).pack(side="left")
        tk.Label(header, text="  SPIKE Prime v5", bg=BG, fg=TEXT,
                 font=("Helvetica", 16, "bold")).pack(side="left")

        self.status_dot = tk.Label(header, text="●", bg=BG, fg=MUTED,
                                   font=("Helvetica", 14))
        self.status_dot.pack(side="right")
        self.status_lbl = tk.Label(header, text="Buscando...", bg=BG, fg=MUTED,
                                   font=("Helvetica", 10))
        self.status_lbl.pack(side="right", padx=(0, 4))

        tk.Frame(self.root, bg="#2A2A2A", height=1).pack(fill="x", padx=PAD, pady=12)

        # ── Battery percentage card ──────────────────────────────────────
        pct_card = tk.Frame(self.root, bg=CARD, relief="flat")
        pct_card.pack(fill="x", padx=PAD, pady=(0, 12))

        tk.Label(pct_card, text="NIVEL DE BATERÍA", bg=CARD, fg=MUTED,
                 font=("Helvetica", 9, "bold")).pack(anchor="w", padx=16, pady=(14, 0))

        self.pct_lbl = tk.Label(pct_card, text="—", bg=CARD, fg=ACCENT,
                                font=("Helvetica", 56, "bold"))
        self.pct_lbl.pack(anchor="w", padx=16)

        # Progress bar canvas
        self.bar_canvas = tk.Canvas(pct_card, bg=CARD, height=14,
                                    highlightthickness=0, relief="flat")
        self.bar_canvas.pack(fill="x", padx=16, pady=(0, 16))
        self.bar_canvas.bind("<Configure>", self._redraw_bar)
        self._bar_pct = 0

        # ── Voltage + Current row ────────────────────────────────────────
        row = tk.Frame(self.root, bg=BG)
        row.pack(fill="x", padx=PAD, pady=(0, PAD))

        self.volt_lbl = self._stat_card(row, "VOLTAJE", "—", "mV", CARD, ACCENT)
        self.volt_lbl.pack(side="left", expand=True, fill="both", padx=(0, 6))

        self.curr_lbl = self._stat_card(row, "CORRIENTE", "—", "mA", CARD, "#FFB800")
        self.curr_lbl.pack(side="left", expand=True, fill="both", padx=(6, 0))

        # ── Refresh button ───────────────────────────────────────────────
        tk.Button(
            self.root, text="⟳  Reiniciar escaneo",
            bg="#1E1E1E", fg=TEXT, activebackground="#2A2A2A",
            activeforeground=ACCENT, relief="flat", cursor="hand2",
            font=("Helvetica", 10), padx=12, pady=8,
            command=self._restart_scan
        ).pack(pady=(0, PAD))

    def _stat_card(self, parent, label, value, unit, bg, color):
        frame = tk.Frame(parent, bg=bg)
        tk.Label(frame, text=label, bg=bg, fg="#666666",
                 font=("Helvetica", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 0))
        val_frame = tk.Frame(frame, bg=bg)
        val_frame.pack(anchor="w", padx=14, pady=(0, 12))
        lbl = tk.Label(val_frame, text=value, bg=bg, fg=color,
                       font=("Helvetica", 28, "bold"))
        lbl.pack(side="left")
        tk.Label(val_frame, text=f" {unit}", bg=bg, fg="#666666",
                 font=("Helvetica", 12)).pack(side="left", anchor="s", pady=4)
        frame._value_label = lbl
        return frame

    def _redraw_bar(self, event=None):
        self.bar_canvas.delete("all")
        w = self.bar_canvas.winfo_width()
        h = 14
        r = 7  # corner radius

        # Background track
        self.bar_canvas.create_rounded_rect = lambda *a, **kw: None
        self._rounded_rect(self.bar_canvas, 0, 0, w, h, r, fill="#2A2A2A", outline="")

        # Fill
        fill_w = max(0, int(w * self._bar_pct / 100))
        if fill_w > 0:
            color = self._bar_color(self._bar_pct)
            self._rounded_rect(self.bar_canvas, 0, 0, fill_w, h, r, fill=color, outline="")

    def _rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, style="pieslice", **kwargs)
        canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, style="pieslice", **kwargs)
        canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, style="pieslice", **kwargs)
        canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, style="pieslice", **kwargs)
        canvas.create_rectangle(x1+r, y1, x2-r, y2, **kwargs)
        canvas.create_rectangle(x1, y1+r, x2, y2-r, **kwargs)

    def _bar_color(self, pct):
        if pct > 60:
            return "#00D4FF"
        elif pct > 30:
            return "#FFB800"
        else:
            return "#FF4444"

    # ── Update UI ─────────────────────────────────────────────────────────

    def _update_ui(self, voltage_mv, current_ma):
        pct = max(0, min(100, int(
            (voltage_mv - BATTERY_EMPTY) / (BATTERY_FULL - BATTERY_EMPTY) * 100
        )))
        self._bar_pct = pct

        self.pct_lbl.config(text=f"{pct}%", fg=self._bar_color(pct))
        self.volt_lbl._value_label.config(text=str(voltage_mv))
        self.curr_lbl._value_label.config(text=str(current_ma))

        self.status_lbl.config(text="Conectado", fg="#00FF88")
        self.status_dot.config(fg="#00FF88")

        self._redraw_bar()

    def _set_scanning(self, scanning: bool):
        if scanning:
            self.status_lbl.config(text="Buscando...", fg="#666666")
            self.status_dot.config(fg="#666666")
        else:
            self.status_lbl.config(text="Sin señal", fg="#FF4444")
            self.status_dot.config(fg="#FF4444")

    # ── BLE ───────────────────────────────────────────────────────────────

    def _start_ble_loop(self):
        self._ble_thread = threading.Thread(target=self._run_ble_loop, daemon=True)
        self._ble_thread.start()

    def _run_ble_loop(self):
        asyncio.run(self._ble_scan_loop())

    async def _ble_scan_loop(self):
        self._scanning = True
        self.root.after(0, self._set_scanning, True)

        def detection_callback(device, advertisement_data):
            mfr = advertisement_data.manufacturer_data
            if PYBRICKS_MFR_ID not in mfr:
                return
            data = mfr[PYBRICKS_MFR_ID]
            result = parse_pybricks_advertisement(data)
            if result:
                voltage, current = result
                self.root.after(0, self._update_ui, voltage, current)

        async with BleakScanner(detection_callback=detection_callback) as scanner:
            # Escanear indefinidamente
            while True:
                await asyncio.sleep(1)

    def _restart_scan(self):
        self._set_scanning(True)
        self.pct_lbl.config(text="—", fg="#00D4FF")
        self.volt_lbl._value_label.config(text="—")
        self.curr_lbl._value_label.config(text="—")
        self._bar_pct = 0
        self._redraw_bar()
        # El thread de BLE es daemon y ya está corriendo continuamente


def main():
    root = tk.Tk()
    root.minsize(380, 320)
    app = SpikeBatteryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()