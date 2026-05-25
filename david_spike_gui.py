"""
spike_drive_gui.py  —  WRO 2026 SPIKE Prime Controller
Controla el SPIKE Prime v5 vía BLE broadcast (Pybricks).

Instala:
    pip install winrt-Windows.Devices.Bluetooth.Advertisement
    pip install winrt-Windows.Storage.Streams

Flujo:
    1. Sube spike_drive_receiver.py al hub con Pybricks Code.
    2. Desconecta Pybricks Code.
    3. Presiona el botón central del hub para arrancarlo.
    4. Corre este script.
"""

import struct
import threading
import tkinter as tk

# ── Protocolo Pybricks ───────────────────────────────────────────────────────
PYBRICKS_MFR_ID = 0x0397
CONTROL_CHANNEL = 1
TYPE_INT = 3

def _enc(value: int) -> bytes:
    if -128 <= value <= 127:
        return bytes([(TYPE_INT << 5) | 1]) + struct.pack("b", value)
    elif -32768 <= value <= 32767:
        return bytes([(TYPE_INT << 5) | 2]) + struct.pack("<h", value)
    else:
        return bytes([(TYPE_INT << 5) | 4]) + struct.pack("<i", value)

def build_payload(speed: int, turn: int) -> bytes:
    return bytes([CONTROL_CHANNEL]) + _enc(speed) + _enc(turn)

TURN_RATE = 200   # deg/s

# ── BLE Advertiser ───────────────────────────────────────────────────────────
class BLEAdvertiser:
    def __init__(self):
        self._publisher = None
        self._lock = threading.Lock()

    def _make_ibuffer(self, data: bytes):
        """
        Convierte bytes → IBuffer usando DataWriter de WinRT.
        write_bytes() espera un array-like indexable, no una list.
        """
        from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream
        writer = DataWriter()
        # El método correcto en python-winrt es write_bytes con un bytes object
        for b in data:
            writer.write_byte(b)          # write_byte(uint8) — uno por uno, seguro
        return writer.detach_buffer()

    def send(self, speed: int, turn: int):
        try:
            from winrt.windows.devices.bluetooth.advertisement import (
                BluetoothLEAdvertisementPublisher,
                BluetoothLEAdvertisement,
                BluetoothLEManufacturerData,
            )

            payload = build_payload(speed, turn)

            mfr = BluetoothLEManufacturerData()
            mfr.company_id = PYBRICKS_MFR_ID
            mfr.data = self._make_ibuffer(payload)

            adv = BluetoothLEAdvertisement()
            adv.manufacturer_data.append(mfr)

            new_pub = BluetoothLEAdvertisementPublisher(adv)

            with self._lock:
                if self._publisher is not None:
                    try:
                        self._publisher.stop()
                    except Exception:
                        pass
                self._publisher = new_pub
                new_pub.start()

        except Exception as e:
            print(f"[BLE] Error: {e}")

    def stop(self):
        with self._lock:
            if self._publisher:
                try:
                    self._publisher.stop()
                except Exception:
                    pass
                self._publisher = None


# ── GUI ───────────────────────────────────────────────────────────────────────
BG    = "#0F0F0F"
CARD  = "#1A1A1A"
TEXT  = "#FFFFFF"
MUTED = "#555555"
CYAN  = "#00D4FF"
GREEN = "#00FF88"
RED   = "#FF4444"
AMBER = "#FFB800"

class DriveApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SPIKE Prime — WRO 2026")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self._ble       = BLEAdvertiser()
        self._keys      = set()
        self._btn       = None
        self._last      = (None, None)
        self.speed_var  = tk.IntVar(value=300)

        self._build()
        self._bind_keys()
        self._loop()

    def _build(self):
        P = 20

        # ── Header ──
        h = tk.Frame(self.root, bg=BG)
        h.pack(fill="x", padx=P, pady=(P, 0))
        tk.Label(h, text="SPIKE Prime v5", bg=BG, fg=TEXT,
                 font=("Helvetica", 15, "bold")).pack(side="left")
        self.status = tk.Label(h, text="● Listo", bg=BG, fg=GREEN,
                               font=("Helvetica", 10))
        self.status.pack(side="right")

        tk.Frame(self.root, bg="#252525", height=1).pack(fill="x", padx=P, pady=10)

        # ── D-pad ──
        pad = tk.Frame(self.root, bg=BG)
        pad.pack(padx=P, pady=(0, P))

        bkw = dict(width=5, height=2, relief="flat", cursor="hand2",
                   font=("Helvetica", 22), bg=CARD, fg=TEXT,
                   activebackground="#1E3A4A", activeforeground=CYAN)

        tk.Label(pad, bg=BG, width=5, height=2).grid(row=0, column=0, padx=4, pady=4)
        self.b_fwd   = tk.Button(pad, text="▲", **bkw)
        self.b_fwd.grid(row=0, column=1, padx=4, pady=4)
        tk.Label(pad, bg=BG, width=5, height=2).grid(row=0, column=2, padx=4, pady=4)

        self.b_left  = tk.Button(pad, text="◀", **bkw)
        self.b_left.grid(row=1, column=0, padx=4, pady=4)
        self.b_stop  = tk.Button(pad, text="⏹", width=5, height=2,
                                 relief="flat", cursor="hand2",
                                 font=("Helvetica", 22), bg="#1E1E1E",
                                 fg=RED, activebackground="#2A2A2A",
                                 activeforeground=RED)
        self.b_stop.grid(row=1, column=1, padx=4, pady=4)
        self.b_right = tk.Button(pad, text="▶", **bkw)
        self.b_right.grid(row=1, column=2, padx=4, pady=4)

        tk.Label(pad, bg=BG, width=5, height=2).grid(row=2, column=0, padx=4, pady=4)
        self.b_back  = tk.Button(pad, text="▼", **bkw)
        self.b_back.grid(row=2, column=1, padx=4, pady=4)
        tk.Label(pad, bg=BG, width=5, height=2).grid(row=2, column=2, padx=4, pady=4)

        for btn, act in [(self.b_fwd,"fwd"),(self.b_back,"back"),
                         (self.b_left,"left"),(self.b_right,"right")]:
            btn.bind("<ButtonPress-1>",   lambda e, a=act: self._press(a))
            btn.bind("<ButtonRelease-1>", lambda e: self._release())
        self.b_stop.bind("<ButtonPress-1>", lambda e: self._estop())

        # ── Velocidad ──
        tk.Frame(self.root, bg="#252525", height=1).pack(fill="x", padx=P)
        sf = tk.Frame(self.root, bg=BG)
        sf.pack(fill="x", padx=P, pady=10)
        tk.Label(sf, text="Velocidad", bg=BG, fg=MUTED,
                 font=("Helvetica", 9)).pack(side="left")
        tk.Scale(sf, variable=self.speed_var, from_=50, to=600,
                 orient="horizontal", bg=BG, fg=TEXT, troughcolor="#2A2A2A",
                 highlightthickness=0, sliderrelief="flat",
                 activebackground=CYAN, length=210).pack(side="right")

        self.cmd_lbl = tk.Label(self.root, text="speed=0  turn=0",
                                bg=BG, fg=MUTED, font=("Courier", 9))
        self.cmd_lbl.pack(pady=(0, 6))
        tk.Label(self.root, text="Teclado: W A S D  /  ↑ ← ↓ →",
                 bg=BG, fg="#333", font=("Helvetica", 8)).pack(pady=(0, P))

    # ── Botones ───────────────────────────────────────────────────────────────
    def _press(self, action):
        self._btn = action
        self._hi(action, True)

    def _release(self):
        if self._btn:
            self._hi(self._btn, False)
        self._btn = None

    def _hi(self, action, on):
        m = {"fwd": self.b_fwd, "back": self.b_back,
             "left": self.b_left, "right": self.b_right}
        b = m.get(action)
        if b:
            b.config(bg="#1E3A4A" if on else CARD, fg=CYAN if on else TEXT)

    def _estop(self):
        self._btn = None
        self._keys.clear()
        self._do_send(0, 0)

    # ── Teclado ───────────────────────────────────────────────────────────────
    def _bind_keys(self):
        self.root.bind("<KeyPress>",   lambda e: self._keys.add(e.keysym.lower()))
        self.root.bind("<KeyRelease>", lambda e: self._keys.discard(e.keysym.lower()))
        self.root.focus_set()

    # ── Loop de control (100 ms = misma frecuencia que hub.ble.observe) ───────
    def _loop(self):
        speed, turn = self._compute()
        if (speed, turn) != self._last:
            self._do_send(speed, turn)
            self._last = (speed, turn)
        self.root.after(100, self._loop)

    def _compute(self):
        s = self.speed_var.get()
        k, b = self._keys, self._btn
        fwd   = "w" in k or "up"    in k or b == "fwd"
        back  = "s" in k or "down"  in k or b == "back"
        left  = "a" in k or "left"  in k or b == "left"
        right = "d" in k or "right" in k or b == "right"
        speed = s if fwd else (-s if back else 0)
        turn  = TURN_RATE if right else (-TURN_RATE if left else 0)
        return speed, turn

    def _do_send(self, speed: int, turn: int):
        threading.Thread(target=self._ble.send, args=(speed, turn), daemon=True).start()
        moving = speed != 0 or turn != 0
        self.status.config(
            text=f"● {'Moviendo' if moving else 'Detenido'}",
            fg=GREEN if moving else AMBER)
        self.cmd_lbl.config(text=f"speed={speed:+4d} mm/s  |  turn={turn:+4d} °/s")


def main():
    root = tk.Tk()
    root.minsize(340, 380)
    app = DriveApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app._ble.stop(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()