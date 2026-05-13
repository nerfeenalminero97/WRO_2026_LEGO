# ============================================================
# spike_battery_broadcast.py
# Corre este script en el SPIKE Prime v5 con Pybricks.
# Hace broadcast del voltaje y corriente de batería por BLE.
# ============================================================

from pybricks.hubs import PrimeHub
from pybricks.tools import wait

# Canal 0: donde se transmite la batería
hub = PrimeHub(broadcast_channel=0)

while True:
    voltage = hub.battery.voltage()   # mV
    current = hub.battery.current()   # mA

    # Broadcast: (voltaje_mV, corriente_mA)
    hub.ble.broadcast((voltage, current))

    # Actualizar cada 500ms
    wait(500)
    
    