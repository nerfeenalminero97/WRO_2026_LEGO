"""
prueba_rotaciones.py
Hace 3 movimientos de 0.25 rotaciones hacia adelante con pausa entre cada uno.
Basado en el protocolo BLE de mapgui.py.
"""

import math, struct, time, threading

# ── Constantes del protocolo ─────────────────────────────────────
PYBRICKS_MFR_ID = 0x0397
TX_CHANNEL      = 1
TYPE_INT        = 3
WHEEL_CIRC_MM   = math.pi * 86.0   # mm por rotación de rueda (~270 mm)

SPEED     = 200    # mm/s
ROTACIONES = 0.25  # rotaciones por movimiento
PAUSAS_S   = 1.0   # segundos de pausa entre movimientos

# ── Codificación del comando ─────────────────────────────────────
def _enc(v: int) -> bytes:
    v = int(v)
    if -128 <= v <= 127:
        return bytes([(TYPE_INT << 5) | 1]) + struct.pack("b", v)
    elif -32768 <= v <= 32767:
        return bytes([(TYPE_INT << 5) | 2]) + struct.pack("<h", v)
    else:
        return bytes([(TYPE_INT << 5) | 4]) + struct.pack("<i", v)

def encode_cmd(speed, turn=0, mc=0, mv=0, tc=0) -> bytes:
    return (bytes([TX_CHANNEL])
            + _enc(speed) + _enc(turn)
            + _enc(mc) + _enc(mv)
            + _enc(tc))

# ── Publicador BLE ───────────────────────────────────────────────
def _make_ibuf(data):
    from winrt.windows.storage.streams import DataWriter
    w = DataWriter()
    for b in data:
        w.write_byte(b)
    return w.detach_buffer()

def _send_ble(speed, turn=0, mc=0, mv=0, tc=0):
    from winrt.windows.devices.bluetooth.advertisement import (
        BluetoothLEAdvertisementPublisher,
        BluetoothLEAdvertisement,
        BluetoothLEManufacturerData,
    )
    mfr = BluetoothLEManufacturerData()
    mfr.company_id = PYBRICKS_MFR_ID
    mfr.data = _make_ibuf(encode_cmd(speed, turn, mc, mv, tc))
    adv = BluetoothLEAdvertisement()
    adv.manufacturer_data.append(mfr)
    pub = BluetoothLEAdvertisementPublisher(adv)
    pub.start()
    return pub

# ── Movimiento de N rotaciones — encoder-based via drive.straight() ──
# El hub ejecuta drive.straight(dist_mm) internamente con PID de encoder.
# El PC solo espera un tiempo generoso; la precisión la maneja el hub.
def mover(rotaciones, velocidad=SPEED):
    dist_mm = int(rotaciones * WHEEL_CIRC_MM)
    espera_s = rotaciones * WHEEL_CIRC_MM / velocidad * 2.0  # buffer generoso
    print(f"  → drive.straight({dist_mm} mm)  [{rotaciones} rot, espera {espera_s:.1f}s]")

    # mc=4 → hub ejecuta drive.straight(motor_val)
    pub = _send_ble(speed=0, turn=0, mc=4, mv=dist_mm)
    time.sleep(espera_s)
    pub.stop()
    time.sleep(0.1)
    print("  ✓ Listo")

# ── Main ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Prueba: 3 movimientos de {ROTACIONES} rotaciones ({ROTACIONES * WHEEL_CIRC_MM:.1f} mm cada uno)\n")

    for i in range(1, 4):
        print(f"Movimiento {i}/3")
        mover(ROTACIONES)
        if i < 3:
            print(f"  Pausa {PAUSAS_S}s...")
            time.sleep(PAUSAS_S)

    print("\nPrueba completada.")
