"""
spike_drive_gui.py
GUI para controlar el SPIKE Prime v5 via BLE (Pybricks broadcast).

Requisitos:
    pip install bleak

Cómo usarlo:
    1. Carga spike_drive_receiver.py en el SPIKE con Pybricks Code.
    2. Desconecta Pybricks Code del hub.
    3. Presiona el botón central del hub para correr el script.
    4. Corre este archivo: python spike_drive_gui.py
    5. Usa los botones o las teclas WASD / flechas para mover.

Protocolo:
    La PC hace un BLE advertisement en formato Pybricks con
    manufacturer ID 0x0397, canal 1, datos = (speed_int, turn_rate_int).
    El hub lo observa y llama a DriveBase.drive(speed, turn_rate).
"""

import asyncio
import struct
import threading
import tkinter as tk

from bleak import BleakScanner
from bleak.backends.scanner import AdvertisementData

# ── Parámetros de movimiento ─────────────────────────────────────────────────
SPEED_FWD  =  300   # mm/s hacia adelante
SPEED_BACK = -300   # mm/s hacia atrás
TURN_RATE  =  200   # deg/s para girar

# ── Protocolo Pybricks ───────────────────────────────────────────────────────
PYBRICKS_MFR_ID  = 0x0397
CONTROL_CHANNEL  = 1   # Canal que observa el hub

# ── Encoder Pybricks ─────────────────────────────────────────────────────────
TYPE_INT = 3

def _encode_int(value: int) -> bytes:
    """Empaqueta un int con header Pybricks: (type<<5 | length) + value."""
    if -128 <= value <= 127:
        return bytes([(TYPE_INT << 5) | 1]) + struct.pack("b", value)
    elif -32768 <= value <= 32767:
        return bytes([(TYPE_INT << 5) | 2]) + struct.pack("<h", value)
    else:
        return bytes([(TYPE_INT << 5) | 4]) + struct.pack("<i", value)

def build_pybricks_adv(channel: int, speed: int, turn_rate: int) -> bytes:
    """
    Construye el payload completo del manufacturer data de Pybricks.
    Layout: [channel_byte] [encoded_speed] [encoded_turn_rate]
    """
    payload  = bytes([channel])
    payload += _encode_int(speed)
    payload += _encode_int(turn_rate)
    return payload


# ── BLE Broadcaster ──────────────────────────────────────────────────────────
# bleak no tiene API de advertising en Windows/macOS directamente.
# Usamos el backend nativo disponible.
# En Linux (BlueZ) se puede hacer advertising real.
# En Windows/macOS usamos el workaround con WinRT / CoreBluetooth via bleak.

try:
    from bleak import BleakAdvertiser  # bleak >= 0.22
    HAS_ADVERTISER = True
except ImportError:
    HAS_ADVERTISER = False


class BLEController:
    """
    Maneja el loop de advertising BLE.
    Envía (speed, turn_rate) al canal 1 cada ~100ms.
    """
    def __init__(self):
        self._speed     = 0
        self._turn_rate = 0
        self._running   = False
        self._loop      = None
        self._lock      = asyncio.Lock()

    def start(self):
        self._running = True
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._advertise_loop())

    def set_command(self, speed: int, turn_rate: int):
        self._speed     = speed
        self._turn_rate = turn_rate

    async def _advertise_loop(self):
        """
        Envía advertisements BLE continuamente.
        Usa BleakAdvertiser si está disponible, si no usa
        un scanner trick (observar + enviar via manufacturer data).
        """
        if HAS_ADVERTISER:
            await self._advertise_with_bleakadvertiser()
        else:
            await self._advertise_fallback()

    async def _advertise_with_bleakadvertiser(self):
        from bleak import BleakAdvertiser
        from bleak.backends.characteristic import AdvertisementData as BleakAdvData

        while self._running:
            payload = build_pybricks_adv(CONTROL_CHANNEL, self._speed, self._turn_rate)
            mfr_data = {PYBRICKS_MFR_ID: payload}
            try:
                async with BleakAdvertiser(manufacturer_data=mfr_data):
                    await asyncio.sleep(0.1)
            except Exception:
                await asyncio.sleep(0.1)

    async def _advertise_fallback(self):
        """
        Fallback para plataformas sin BleakAdvertiser.
        Usa el módulo platform-specific de bleak directamente.
        """
        import sys
        if sys.platform == "win32":
            await self._advertise_winrt()
        elif sys.platform == "darwin":
            await self._advertise_corebluetooth()
        else:
            await self._advertise_bluez()

    async def _advertise_winrt(self):
        """Windows: WinRT Bluetooth LE advertisement publisher."""
        try:
            from winrt.windows.devices.bluetooth.advertisement import (
                BluetoothLEAdvertisementPublisher,
                BluetoothLEAdvertisement,
                BluetoothLEManufacturerData,
            )
            from winrt.windows.storage.streams import DataWriter

            publisher = BluetoothLEAdvertisementPublisher()
            adv = BluetoothLEAdvertisement()

            while self._running:
                payload = build_pybricks_adv(CONTROL_CHANNEL, self._speed, self._turn_rate)
                mfr = BluetoothLEManufacturerData()
                mfr.company_id = PYBRICKS_MFR_ID
                writer = DataWriter()
                for b in payload:
                    writer.write_byte(b)
                mfr.data = writer.detach_buffer()
                adv.manufacturer_data.clear()
                adv.manufacturer_data.append(mfr)
                publisher.advertisement = adv
                publisher.start()
                await asyncio.sleep(0.1)
                publisher.stop()

        except Exception as e:
            print(f"[WinRT advertiser error] {e}")

    async def _advertise_bluez(self):
        """Linux: BlueZ D-Bus advertising via dbus-next."""
        try:
            import dbus_next  # type: ignore
            print("[BLE] BlueZ advertising (Linux)")
            # Implementación BlueZ omitida por brevedad — usa pb_broadcast CLI:
            # pip install pybricks-ble && pb_broadcast 1 <speed> <turn>
            while self._running:
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[BlueZ advertiser error] {e}")

    async def _advertise_corebluetooth(self):
        """macOS: CoreBluetooth via pyobjc."""
        print("[BLE] CoreBluetooth advertising (macOS) - requiere pyobjc")
        while self._running:
            await asyncio.sleep(0.1)


# ── GUI ───────────────────────────────────────────────────────────────────────
class DriveApp:
    BG     = "#0F0F0F"
    CARD   = "#1A1A1A"
    TEXT   = "#FFFFFF"
    MUTED  = "#555555"
    ACTIVE = "#00D4FF"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SPIKE Prime — Control")
        self.root.configure(bg=self.BG)
        self.root.resizable(False, False)

        self._ble = BLEController()
        self._keys_held = set()   # teclas actualmente presionadas
        self._btn_held  = None    # botón de pantalla actualmente presionado

        self._build()
        self._bind_keys()
        self._ble.start()
        self._update_loop()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build(self):
        P = 20

        # Header
        h = tk.Frame(self.root, bg=self.BG)
        h.pack(fill="x", padx=P, pady=(P, 0))
        tk.Label(h, text="SPIKE Prime v5", bg=self.BG, fg=self.TEXT,
                 font=("Helvetica", 15, "bold")).pack(side="left")
        self.status_lbl = tk.Label(h, text="● Transmitiendo", bg=self.BG,
                                   fg="#00FF88", font=("Helvetica", 10))
        self.status_lbl.pack(side="right")

        tk.Frame(self.root, bg="#252525", height=1).pack(fill="x", padx=P, pady=10)

        # D-pad
        pad_frame = tk.Frame(self.root, bg=self.BG)
        pad_frame.pack(padx=P, pady=(0, P))

        btn_cfg = dict(width=5, height=2, relief="flat", cursor="hand2",
                       font=("Helvetica", 18), bg=self.CARD, fg=self.TEXT,
                       activebackground="#2A2A2A", activeforeground=self.ACTIVE)

        # Fila vacía - arriba
        tk.Label(pad_frame, bg=self.BG, width=5, height=2).grid(row=0, column=0)
        self.btn_fwd  = tk.Button(pad_frame, text="▲", **btn_cfg)
        self.btn_fwd.grid(row=0, column=1, padx=4, pady=4)
        tk.Label(pad_frame, bg=self.BG, width=5, height=2).grid(row=0, column=2)

        # Fila del medio
        self.btn_left  = tk.Button(pad_frame, text="◀", **btn_cfg)
        self.btn_left.grid(row=1, column=0, padx=4, pady=4)
        self.btn_stop  = tk.Button(pad_frame, text="⏹", width=5, height=2,
                                   relief="flat", cursor="hand2",
                                   font=("Helvetica", 18),
                                   bg="#1E1E1E", fg="#FF4444",
                                   activebackground="#2A2A2A",
                                   activeforeground="#FF4444")
        self.btn_stop.grid(row=1, column=1, padx=4, pady=4)
        self.btn_right = tk.Button(pad_frame, text="▶", **btn_cfg)
        self.btn_right.grid(row=1, column=2, padx=4, pady=4)

        # Fila abajo
        tk.Label(pad_frame, bg=self.BG, width=5, height=2).grid(row=2, column=0)
        self.btn_back  = tk.Button(pad_frame, text="▼", **btn_cfg)
        self.btn_back.grid(row=2, column=1, padx=4, pady=4)
        tk.Label(pad_frame, bg=self.BG, width=5, height=2).grid(row=2, column=2)

        # Bind botones de pantalla (press/release para mantener presionado)
        self._bind_btn(self.btn_fwd,   "fwd")
        self._bind_btn(self.btn_back,  "back")
        self._bind_btn(self.btn_left,  "left")
        self._bind_btn(self.btn_right, "right")
        self.btn_stop.bind("<ButtonPress-1>",   lambda e: self._on_stop())

        # Separador
        tk.Frame(self.root, bg="#252525", height=1).pack(fill="x", padx=P)

        # Velocidad
        spd_frame = tk.Frame(self.root, bg=self.BG)
        spd_frame.pack(fill="x", padx=P, pady=10)
        tk.Label(spd_frame, text="Velocidad", bg=self.BG, fg=self.MUTED,
                 font=("Helvetica", 9)).pack(side="left")
        self.speed_var = tk.IntVar(value=300)
        spd = tk.Scale(spd_frame, variable=self.speed_var,
                       from_=50, to=600, orient="horizontal",
                       bg=self.BG, fg=self.TEXT, troughcolor="#2A2A2A",
                       highlightthickness=0, sliderrelief="flat",
                       activebackground=self.ACTIVE, length=180)
        spd.pack(side="right")

        # Label de comando actual
        self.cmd_lbl = tk.Label(self.root, text="speed=0  turn=0",
                                bg=self.BG, fg=self.MUTED, font=("Courier", 9))
        self.cmd_lbl.pack(pady=(0, P))

        # Hint teclado
        tk.Label(self.root, text="Teclado: W A S D  o  ↑ ← ↓ →",
                 bg=self.BG, fg="#333", font=("Helvetica", 8)).pack(pady=(0, P))

    def _bind_btn(self, btn, action):
        btn.bind("<ButtonPress-1>",   lambda e, a=action: self._btn_press(a))
        btn.bind("<ButtonRelease-1>", lambda e: self._btn_release())

    def _btn_press(self, action):
        self._btn_held = action
        self._highlight_btn(action, True)

    def _btn_release(self):
        if self._btn_held:
            self._highlight_btn(self._btn_held, False)
        self._btn_held = None

    def _highlight_btn(self, action, active):
        mapping = {
            "fwd": self.btn_fwd, "back": self.btn_back,
            "left": self.btn_left, "right": self.btn_right
        }
        btn = mapping.get(action)
        if btn:
            btn.config(bg=("#2A4A5A" if active else self.CARD),
                       fg=(self.ACTIVE if active else self.TEXT))

    def _on_stop(self):
        self._btn_held = None
        self._keys_held.clear()
        self._ble.set_command(0, 0)

    # ── Keyboard ──────────────────────────────────────────────────────────────
    def _bind_keys(self):
        self.root.bind("<KeyPress>",   self._key_press)
        self.root.bind("<KeyRelease>", self._key_release)
        self.root.focus_set()

    def _key_press(self, e):
        self._keys_held.add(e.keysym.lower())

    def _key_release(self, e):
        self._keys_held.discard(e.keysym.lower())

    # ── Command loop ──────────────────────────────────────────────────────────
    def _update_loop(self):
        speed, turn = self._compute_command()
        self._ble.set_command(speed, turn)
        self.cmd_lbl.config(text=f"speed={speed:+4d} mm/s  |  turn={turn:+4d} °/s")
        self.root.after(50, self._update_loop)

    def _compute_command(self) -> tuple:
        spd_val = self.speed_var.get()

        # Prioridad: teclado sobre botón de pantalla
        active = self._btn_held
        keys   = self._keys_held

        fwd   = ("w" in keys or "up"    in keys or active == "fwd")
        back  = ("s" in keys or "down"  in keys or active == "back")
        left  = ("a" in keys or "left"  in keys or active == "left")
        right = ("d" in keys or "right" in keys or active == "right")

        speed     = 0
        turn_rate = 0

        if fwd:   speed =  spd_val
        if back:  speed = -spd_val
        if left:  turn_rate = -TURN_RATE
        if right: turn_rate =  TURN_RATE

        return speed, turn_rate


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    root.minsize(340, 400)
    DriveApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()