# mision_gui.py  —  WRO 2026 Mosaic Masters
#
# GUI de competencia para:
#   1. Seleccionar el patrón del mosaico (12 celdas, 4×3)
#   2. Enviar el patrón al hub vía BLE  (motor_cmd=5)
#   3. Iniciar la misión autónoma       (motor_cmd=6)
#
# Requiere Windows (winrt para BLE TX).
# pip install winrt-Windows.Devices.Bluetooth.Advertisement
# pip install winrt-Windows.Storage.Streams
#
# Usar junto con wro_autonomo.py en el hub.
# ════════════════════════════════════════════════════════════════

import struct, threading, time
import tkinter as tk
from tkinter import messagebox

# ════════════════════════════════════════════════════════════════
#  PROTOCOLO PYBRICKS (mismo que mapgui.py)
# ════════════════════════════════════════════════════════════════
PYBRICKS_MFR_ID = 0x0397
TX_CHANNEL      = 1
TYPE_INT        = 3

def _enc(v: int) -> bytes:
    v = int(v)
    if -128 <= v <= 127:
        return bytes([(TYPE_INT << 5) | 1]) + struct.pack("b", v)
    elif -32768 <= v <= 32767:
        return bytes([(TYPE_INT << 5) | 2]) + struct.pack("<h", v)
    else:
        return bytes([(TYPE_INT << 5) | 4]) + struct.pack("<i", v)

def encode_cmd(speed=0, turn=0, motor_cmd=0, motor_val=0, turn_cmd=0) -> bytes:
    return (bytes([TX_CHANNEL])
            + _enc(speed) + _enc(turn)
            + _enc(motor_cmd) + _enc(motor_val)
            + _enc(turn_cmd))

# ════════════════════════════════════════════════════════════════
#  BLE PUBLISHER (mismo que mapgui.py)
# ════════════════════════════════════════════════════════════════
class BLEPublisher:
    REFRESH_S = 2.0

    def __init__(self):
        self._speed = self._turn = self._mc = self._mv = self._tc = 0
        self._changed  = threading.Event()
        self._stop_evt = threading.Event()
        threading.Thread(target=self._loop, daemon=True).start()

    def _ibuf(self, data):
        from winrt.windows.storage.streams import DataWriter
        w = DataWriter()
        for b in data:
            w.write_byte(b)
        return w.detach_buffer()

    def _make_pub(self, s, t, mc, mv, tc):
        from winrt.windows.devices.bluetooth.advertisement import (
            BluetoothLEAdvertisementPublisher,
            BluetoothLEAdvertisement,
            BluetoothLEManufacturerData,
        )
        mfr = BluetoothLEManufacturerData()
        mfr.company_id = PYBRICKS_MFR_ID
        mfr.data = self._ibuf(encode_cmd(s, t, mc, mv, tc))
        adv = BluetoothLEAdvertisement()
        adv.manufacturer_data.append(mfr)
        pub = BluetoothLEAdvertisementPublisher(adv)
        pub.start()
        return pub

    def _loop(self):
        pub = None
        cur = (None,) * 5
        last_ref = 0.0
        while not self._stop_evt.is_set():
            self._changed.wait(timeout=self.REFRESH_S)
            self._changed.clear()
            if self._stop_evt.is_set():
                break
            nxt = (self._speed, self._turn, self._mc, self._mv, self._tc)
            now = time.monotonic()
            if nxt != cur or (now - last_ref) >= self.REFRESH_S or pub is None:
                if pub:
                    try:
                        pub.stop()
                    except Exception:
                        pass
                try:
                    pub = self._make_pub(*nxt)
                    cur = nxt
                    last_ref = now
                except Exception as e:
                    print(f"[BLE TX] {e}")
                    pub = None
        if pub:
            try:
                pub.stop()
            except Exception:
                pass

    def send(self, speed=0, turn=0, mc=0, mv=0, tc=0):
        changed = (speed, turn, mc, mv, tc) != (self._speed, self._turn, self._mc, self._mv, self._tc)
        self._speed = speed
        self._turn  = turn
        self._mc    = mc
        self._mv    = mv
        self._tc    = tc
        if changed:
            self._changed.set()

    def stop(self):
        self._stop_evt.set()
        self._changed.set()

# ════════════════════════════════════════════════════════════════
#  PATRÓN DEL MOSAICO
# ════════════════════════════════════════════════════════════════
COLOR_CYCLE   = ["Y", "B", "G", "W"]           # orden de ciclo al hacer click
COLOR_LABEL   = {"Y": "Y", "B": "A", "G": "V", "W": "B"}  # etiqueta en botón
COLOR_HEX     = {"Y": "#FFD600", "B": "#1565C0", "G": "#2E7D32", "W": "#EEEEEE"}
COLOR_FG      = {"Y": "#000000", "B": "#FFFFFF", "G": "#FFFFFF", "W": "#000000"}
COLOR_ENCODE  = {"Y": 0, "B": 1, "G": 2, "W": 3}  # 2 bits por celda

def pack_pattern(pattern: list[str]) -> int:
    """Empaqueta 12 colores ['Y','B',...] en un int32 (2 bits por celda)."""
    packed = 0
    for i, c in enumerate(pattern):
        packed |= (COLOR_ENCODE[c] << (i * 2))
    return packed

# ════════════════════════════════════════════════════════════════
#  APP
# ════════════════════════════════════════════════════════════════
class MisionApp:
    """
    Ventana de competencia. Layout:

        ┌────────────────────────────────┐
        │   PATRON DEL MOSAICO  (título) │
        │                                │
        │  [C0][C1][C2]  ← fila 0        │
        │  [C3][C4][C5]  ← fila 1        │
        │  [C6][C7][C8]  ← fila 2        │
        │  [C9][C10][C11] ← fila 3       │
        │                                │
        │  [RESET]  [ENVIAR PATRON]       │
        │  [INICIAR MISION]               │
        │                                │
        │  Estado: Sin patrón / OK / …   │
        └────────────────────────────────┘

    Cada celda muestra el color seleccionado.
    Click → cicla Y → A → V → B → Y …
    """

    ROWS = 4
    COLS = 3
    BTN_W = 7    # ancho de cada botón de celda (chars)
    BTN_H = 3    # alto de cada botón (chars)

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WRO 2026 — Misión Mosaico")
        self.root.resizable(False, False)

        self.ble = BLEPublisher()
        self.pattern: list[str] = ["Y"] * 12   # estado inicial: todo amarillo
        self.patron_enviado = False

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Construcción de la UI ─────────────────────────────────────────────────

    def _build_ui(self):
        PAD = 12

        # Título
        tk.Label(
            self.root,
            text="PATRÓN DEL MOSAICO",
            font=("Helvetica", 16, "bold"),
        ).pack(pady=(PAD, 4))

        tk.Label(
            self.root,
            text="Click en cada celda para cambiar color\n(Y=Amarillo  A=Azul  V=Verde  B=Blanco)",
            font=("Helvetica", 9),
            fg="#555555",
        ).pack(pady=(0, 8))

        # Grid de celdas
        frame_grid = tk.Frame(self.root, bd=2, relief=tk.SUNKEN)
        frame_grid.pack(padx=PAD, pady=4)

        self._btns: list[tk.Button] = []
        for row in range(self.ROWS):
            tk.Label(frame_grid, text=f"Fila {row}", font=("Helvetica", 8), fg="#777777").grid(
                row=row, column=self.COLS, padx=(4, 0)
            )
            for col in range(self.COLS):
                idx = row * self.COLS + col
                btn = tk.Button(
                    frame_grid,
                    text=self._btn_text(idx),
                    width=self.BTN_W,
                    height=self.BTN_H,
                    font=("Helvetica", 11, "bold"),
                    bg=COLOR_HEX[self.pattern[idx]],
                    fg=COLOR_FG[self.pattern[idx]],
                    relief=tk.RAISED,
                    bd=2,
                    command=lambda i=idx: self._cycle_color(i),
                )
                btn.grid(row=row, column=col, padx=2, pady=2)
                self._btns.append(btn)

        # Botones de acción
        frame_btns = tk.Frame(self.root)
        frame_btns.pack(pady=(10, 4), padx=PAD, fill=tk.X)

        tk.Button(
            frame_btns, text="RESET (todo Y)", width=14,
            command=self._reset_pattern,
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            frame_btns, text="ENVIAR PATRÓN", width=16,
            bg="#FF8F00", fg="white", font=("Helvetica", 10, "bold"),
            command=self._enviar_patron,
        ).pack(side=tk.LEFT)

        self.btn_iniciar = tk.Button(
            self.root, text="INICIAR MISIÓN",
            bg="#1B5E20", fg="white",
            font=("Helvetica", 13, "bold"),
            height=2, state=tk.DISABLED,
            command=self._iniciar_mision,
        )
        self.btn_iniciar.pack(padx=PAD, pady=6, fill=tk.X)

        # Estado
        self.lbl_estado = tk.Label(
            self.root,
            text="Estado: Sin patrón enviado",
            font=("Helvetica", 10),
            fg="#B71C1C",
            anchor=tk.W,
        )
        self.lbl_estado.pack(padx=PAD, pady=(2, PAD), fill=tk.X)

    # ── Interacción ───────────────────────────────────────────────────────────

    def _btn_text(self, idx: int) -> str:
        c = self.pattern[idx]
        return f"{idx}\n{COLOR_LABEL[c]}"

    def _cycle_color(self, idx: int):
        cur = self.pattern[idx]
        nxt = COLOR_CYCLE[(COLOR_CYCLE.index(cur) + 1) % len(COLOR_CYCLE)]
        self.pattern[idx] = nxt
        btn = self._btns[idx]
        btn.config(
            text=self._btn_text(idx),
            bg=COLOR_HEX[nxt],
            fg=COLOR_FG[nxt],
        )
        # Si el patrón cambia después de enviarlo, avisa que hay que reenviar
        if self.patron_enviado:
            self.patron_enviado = False
            self.btn_iniciar.config(state=tk.DISABLED)
            self._set_estado("Patrón modificado — vuelve a enviar", "#E65100")

    def _reset_pattern(self):
        for i in range(12):
            self.pattern[i] = "Y"
            self._btns[i].config(
                text=self._btn_text(i),
                bg=COLOR_HEX["Y"],
                fg=COLOR_FG["Y"],
            )
        self.patron_enviado = False
        self.btn_iniciar.config(state=tk.DISABLED)
        self._set_estado("Patrón reseteado — vuelve a enviar", "#E65100")

    def _enviar_patron(self):
        packed = pack_pattern(self.pattern)
        try:
            self.ble.send(mc=5, mv=packed)
            time.sleep(0.4)
            self.ble.send(mc=0, mv=0)   # liberar canal
        except Exception as e:
            messagebox.showerror("BLE Error", str(e))
            return

        self.patron_enviado = True
        self.btn_iniciar.config(state=tk.NORMAL)
        colores_txt = " ".join(self.pattern)
        self._set_estado(f"Patrón enviado ✓  |  {colores_txt}", "#1B5E20")
        print(f"[TX] Patrón enviado: {self.pattern}  (packed={packed:#010x})")

    def _iniciar_mision(self):
        if not self.patron_enviado:
            messagebox.showwarning("Sin patrón", "Envía el patrón primero.")
            return
        try:
            self.ble.send(mc=6)
            time.sleep(0.4)
            self.ble.send(mc=0)
        except Exception as e:
            messagebox.showerror("BLE Error", str(e))
            return

        self.btn_iniciar.config(state=tk.DISABLED)
        self._set_estado("Misión iniciada — hub en modo autónomo", "#1565C0")
        print("[TX] Señal INICIAR enviada")

    def _set_estado(self, text: str, color: str = "#000000"):
        self.lbl_estado.config(text=f"Estado: {text}", fg=color)

    def _on_close(self):
        self.ble.stop()
        self.root.destroy()


# ════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app = MisionApp(root)
    root.mainloop()
