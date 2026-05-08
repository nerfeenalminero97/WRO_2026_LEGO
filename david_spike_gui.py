import sys, json, csv, datetime, asyncio
from collections import deque
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QTextEdit, QGroupBox,
    QSizePolicy, QSlider, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygonF
from bleak import BleakScanner, BleakClient

# UUID del servicio serial de Pybricks (oficial)
PYBRICKS_SERVICE_UUID = "c5f50001-8280-46da-89f4-6d8051e4aeef"
PYBRICKS_TX_UUID      = "c5f50002-8280-46da-89f4-6d8051e4aeef"  # PC → Hub
PYBRICKS_RX_UUID      = "c5f50003-8280-46da-89f4-6d8051e4aeef"  # Hub → PC


# ═══════════════════════════════════════════════════════════════
#  BLE Worker — vive en su propio QThread
# ═══════════════════════════════════════════════════════════════
class BLEWorker(QThread):
    telemetry_received = pyqtSignal(dict)
    log_message        = pyqtSignal(str)
    connected_signal   = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._running   = True
        self._cmd_queue = deque()
        self._client    = None

    def send_cmd(self, cmd_dict):
        """Llamado desde el hilo GUI — solo encola, nunca bloquea."""
        self._cmd_queue.append(json.dumps(cmd_dict) + "\n")

    def stop(self):
        self._running = False

    def run(self):
        asyncio.run(self._ble_loop())

    async def _ble_loop(self):
        # ── Escanear y encontrar el SPIKE ────────────────────
        self.log_message.emit("Buscando SPIKE por Bluetooth...")
        try:
            device = await BleakScanner.find_device_by_filter(
                lambda d, _: PYBRICKS_SERVICE_UUID.lower() in
                             [str(u).lower() for u in (d.metadata.get("uuids") or [])],
                timeout=10.0
            )
        except Exception as e:
            self.log_message.emit(f"Error al escanear: {e}")
            self.connected_signal.emit(False)
            return

        if device is None:
            self.log_message.emit("❌ No se encontró el SPIKE. Verifica que esté encendido y con el programa corriendo.")
            self.connected_signal.emit(False)
            return

        self.log_message.emit(f"SPIKE encontrado: {device.name} ({device.address})")

        buf = ""

        def on_notify(_, data: bytearray):
            nonlocal buf
            buf += data.decode(errors="ignore")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if line:
                    try:
                        self.telemetry_received.emit(json.loads(line))
                    except json.JSONDecodeError:
                        self.log_message.emit(f"JSON inválido: {line}")

        # ── Conectar ─────────────────────────────────────────
        try:
            async with BleakClient(device) as client:
                self._client = client
                await client.start_notify(PYBRICKS_RX_UUID, on_notify)
                self.log_message.emit("✅ Conectado por Bluetooth")
                self.connected_signal.emit(True)

                while self._running and client.is_connected:
                    # Enviar comandos encolados
                    while self._cmd_queue:
                        line = self._cmd_queue.popleft()
                        await client.write_gatt_char(
                            PYBRICKS_TX_UUID,
                            line.encode(),
                            response=False
                        )
                    await asyncio.sleep(0.05)

                await client.stop_notify(PYBRICKS_RX_UUID)
        except Exception as e:
            self.log_message.emit(f"Error de conexión: {e}")

        self._client = None
        self.connected_signal.emit(False)
        self.log_message.emit("Bluetooth desconectado.")


# ═══════════════════════════════════════════════════════════════
#  Map widget
# ═══════════════════════════════════════════════════════════════
class MapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(300, 300)
        self.path        = [QPointF(0, 0)]
        self.heading     = 0.0
        self.scale       = 1.0
        self.last_color1 = "NONE"
        self.last_color2 = "NONE"
        self._COLORS = {
            "BLACK":  QColor("#222222"),
            "WHITE":  QColor("#eeeeee"),
            "RED":    QColor("#e24b4a"),
            "GREEN":  QColor("#639922"),
            "BLUE":   QColor("#378add"),
            "YELLOW": QColor("#ef9f27"),
            "NONE":   QColor("#888888"),
        }

    def update_position(self, x, y, heading, c1, c2):
        self.path.append(QPointF(x, y))
        if len(self.path) > 2000:
            self.path = self.path[-2000:]
        self.heading     = heading
        self.last_color1 = c1
        self.last_color2 = c2
        self.update()

    def reset(self):
        self.path    = [QPointF(0, 0)]
        self.heading = 0.0
        self.update()

    def paintEvent(self, _):
        p  = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h   = self.width(), self.height()
        cx, cy = w / 2, h / 2

        p.fillRect(0, 0, w, h, QColor("#1a1a2e"))

        p.setPen(QPen(QColor("#2a2a4a"), 1))
        step = 50
        for gx in range(int(cx % step), w, step):
            p.drawLine(gx, 0, gx, h)
        for gy in range(int(cy % step), h, step):
            p.drawLine(0, gy, w, gy)

        p.setPen(QPen(QColor("#444488"), 2))
        p.drawLine(0, int(cy), w, int(cy))
        p.drawLine(int(cx), 0, int(cx), h)

        p.setPen(QColor("#aaaacc"))
        p.setFont(QFont("monospace", 9))
        p.drawText(int(cx) + 4, int(cy) - 4, "(0,0)")

        if len(self.path) > 1:
            p.setPen(QPen(QColor("#5dcaa5"), 2))
            for i in range(1, len(self.path)):
                x1 = cx + self.path[i-1].x() * self.scale
                y1 = cy - self.path[i-1].y() * self.scale
                x2 = cx + self.path[i].x()   * self.scale
                y2 = cy - self.path[i].y()    * self.scale
                p.drawLine(int(x1), int(y1), int(x2), int(y2))

        if self.path:
            rx = cx + self.path[-1].x() * self.scale
            ry = cy - self.path[-1].y() * self.scale
            p.save()
            p.translate(rx, ry)
            p.rotate(self.heading)
            p.setBrush(QBrush(QColor("#7f77dd")))
            p.setPen(Qt.NoPen)
            triangle = QPolygonF([
                QPointF(0, -12), QPointF(-7, 8), QPointF(7, 8)
            ])
            p.drawPolygon(triangle)
            p.restore()

        p.setBrush(QBrush(self._COLORS.get(self.last_color1, QColor("#888"))))
        p.setPen(QPen(QColor("#555"), 1))
        p.drawEllipse(10, h - 30, 18, 18)
        p.setBrush(QBrush(self._COLORS.get(self.last_color2, QColor("#888"))))
        p.drawEllipse(34, h - 30, 18, 18)
        p.setPen(QColor("#aaaacc"))
        p.setFont(QFont("monospace", 8))
        p.drawText(10, h - 35, "CS-E  CS-A")
        p.end()


# ═══════════════════════════════════════════════════════════════
#  Main window
# ═══════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPIKE Prime Controller")
        self.resize(1100, 700)
        self.worker   = None
        self.log_rows = []
        self._held    = set()
        self._build_ui()
        self._setup_keypress_timer()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(8)
        root.addLayout(left, 0)

        # Conexión
        conn_box = QGroupBox("Conexión Bluetooth")
        conn_lay = QVBoxLayout(conn_box)
        self.btn_connect = QPushButton("🔵  Buscar y Conectar SPIKE")
        self.btn_connect.setMinimumHeight(40)
        self.btn_connect.clicked.connect(self._connect)
        conn_lay.addWidget(self.btn_connect)
        self.btn_disconnect = QPushButton("Desconectar")
        self.btn_disconnect.setEnabled(False)
        self.btn_disconnect.clicked.connect(self._disconnect)
        conn_lay.addWidget(self.btn_disconnect)
        left.addWidget(conn_box)

        # Velocidad
        spd_box = QGroupBox("Velocidad")
        spd_lay = QVBoxLayout(spd_box)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 600)
        self.speed_slider.setValue(300)
        self.speed_label  = QLabel("300 mm/s")
        self.speed_label.setAlignment(Qt.AlignCenter)
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"{v} mm/s"))
        spd_lay.addWidget(self.speed_slider)
        spd_lay.addWidget(self.speed_label)
        left.addWidget(spd_box)

        # Controles
        ctrl_box = QGroupBox("Controles  (también puedes usar WASD o flechas)")
        ctrl_lay = QGridLayout(ctrl_box)
        self.btn_fwd  = QPushButton("▲\nForward")
        self.btn_bwd  = QPushButton("▼\nBackward")
        self.btn_lft  = QPushButton("◀\nLeft")
        self.btn_rgt  = QPushButton("▶\nRight")
        self.btn_stop = QPushButton("■\nStop")
        self.btn_au   = QPushButton("Arm ▲")
        self.btn_ad   = QPushButton("Arm ▼")
        self.btn_rst  = QPushButton("Reset posición (0,0)")

        for btn in [self.btn_fwd, self.btn_bwd, self.btn_lft,
                    self.btn_rgt, self.btn_stop]:
            btn.setMinimumSize(70, 60)

        ctrl_lay.addWidget(self.btn_fwd,  0, 1)
        ctrl_lay.addWidget(self.btn_lft,  1, 0)
        ctrl_lay.addWidget(self.btn_stop, 1, 1)
        ctrl_lay.addWidget(self.btn_rgt,  1, 2)
        ctrl_lay.addWidget(self.btn_bwd,  2, 1)
        ctrl_lay.addWidget(self.btn_au,   3, 0)
        ctrl_lay.addWidget(self.btn_ad,   3, 2)
        ctrl_lay.addWidget(self.btn_rst,  4, 0, 1, 3)

        self.btn_fwd.pressed.connect(lambda: self._cmd("forward"))
        self.btn_fwd.released.connect(lambda: self._cmd("stop"))
        self.btn_bwd.pressed.connect(lambda: self._cmd("backward"))
        self.btn_bwd.released.connect(lambda: self._cmd("stop"))
        self.btn_lft.pressed.connect(lambda: self._cmd("left"))
        self.btn_lft.released.connect(lambda: self._cmd("stop"))
        self.btn_rgt.pressed.connect(lambda: self._cmd("right"))
        self.btn_rgt.released.connect(lambda: self._cmd("stop"))
        self.btn_stop.clicked.connect(lambda: self._cmd("stop"))
        self.btn_au.clicked.connect(lambda: self._cmd("arm_up"))
        self.btn_ad.clicked.connect(lambda: self._cmd("arm_down"))
        self.btn_rst.clicked.connect(self._reset_position)
        left.addWidget(ctrl_box)

        self.btn_export = QPushButton("💾  Exportar log a CSV")
        self.btn_export.clicked.connect(self._export_csv)
        left.addWidget(self.btn_export)
        left.addStretch()

        # Columna derecha
        right = QVBoxLayout()
        root.addLayout(right, 1)

        telem_row = QHBoxLayout()
        self.lbl_x   = self._telem_card("X",         "0.0 mm")
        self.lbl_y   = self._telem_card("Y",         "0.0 mm")
        self.lbl_hdg = self._telem_card("Heading",   "0.0°")
        self.lbl_bat = self._telem_card("Batería",   "—")
        self.lbl_c1  = self._telem_card("Sensor E",  "—")
        self.lbl_c2  = self._telem_card("Sensor A",  "—")
        for card in [self.lbl_x, self.lbl_y, self.lbl_hdg,
                     self.lbl_bat, self.lbl_c1, self.lbl_c2]:
            telem_row.addWidget(card)
        right.addLayout(telem_row)

        self.map_widget = MapWidget()
        self.map_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right.addWidget(self.map_widget, 1)

        log_box = QGroupBox("Log de eventos")
        log_lay = QVBoxLayout(log_box)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(140)
        self.log_view.setFont(QFont("monospace", 10))
        log_lay.addWidget(self.log_view)
        right.addWidget(log_box)

        self.statusBar().showMessage("Sin conexión")

    def _telem_card(self, label, value):
        card = QGroupBox(label)
        lay  = QVBoxLayout(card)
        lbl  = QLabel(value)
        lbl.setFont(QFont("monospace", 13))
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)
        return card

    def _set_telem(self, box, text):
        box.findChild(QLabel).setText(text)

    def _connect(self):
        self.worker = BLEWorker()
        self.worker.telemetry_received.connect(self._on_telemetry)
        self.worker.log_message.connect(self._log)
        self.worker.connected_signal.connect(self._on_connected)
        self.worker.start()
        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("🔍  Buscando...")
        self.statusBar().showMessage("Buscando SPIKE por Bluetooth...")

    def _disconnect(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            self.worker = None
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText("🔵  Buscar y Conectar SPIKE")
        self.btn_disconnect.setEnabled(False)
        self.statusBar().showMessage("Sin conexión")

    @pyqtSlot(bool)
    def _on_connected(self, ok):
        if ok:
            self.btn_connect.setText("✅  Conectado")
            self.btn_disconnect.setEnabled(True)
            self.statusBar().showMessage("Conectado por Bluetooth ✅")
        else:
            self.btn_connect.setEnabled(True)
            self.btn_connect.setText("🔵  Buscar y Conectar SPIKE")
            self.btn_disconnect.setEnabled(False)
            self.statusBar().showMessage("Desconectado")

    def _cmd(self, action):
        if not self.worker:
            return
        speed = self.speed_slider.value()
        self.worker.send_cmd({"cmd": action, "speed": speed})
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._log(f"[{ts}] CMD → {action}  speed={speed}")
        self.log_rows.append({
            "timestamp": ts, "type": "cmd",
            "action": action, "speed": speed,
            "x": "", "y": "", "heading": "",
            "color1": "", "color2": ""
        })

    def _reset_position(self):
        self._cmd("reset_pos")
        self.map_widget.reset()

    @pyqtSlot(dict)
    def _on_telemetry(self, data):
        if "error" in data:
            self._log(f"Error hub: {data['error']}")
            return
        if "msg" in data:
            self._log(f"Hub: {data['msg']}")
            return

        x   = data.get("x", 0)
        y   = data.get("y", 0)
        hdg = data.get("heading", 0)
        bat = data.get("battery", 0)
        c1  = data.get("color1", "NONE")
        c2  = data.get("color2", "NONE")
        r1  = data.get("ref1", 0)
        r2  = data.get("ref2", 0)

        self._set_telem(self.lbl_x,   f"{x:.1f} mm")
        self._set_telem(self.lbl_y,   f"{y:.1f} mm")
        self._set_telem(self.lbl_hdg, f"{hdg:.1f}°")
        self._set_telem(self.lbl_bat, f"{bat}%")
        self._set_telem(self.lbl_c1,  f"{c1}\n({r1}%)")
        self._set_telem(self.lbl_c2,  f"{c2}\n({r2}%)")

        self.map_widget.update_position(x, y, hdg, c1, c2)

        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_rows.append({
            "timestamp": ts, "type": "telem",
            "action": "", "speed": "",
            "x": x, "y": y, "heading": hdg,
            "color1": c1, "color2": c2
        })

    def _setup_keypress_timer(self):
        self._key_timer = QTimer()
        self._key_timer.setInterval(50)
        self._key_timer.timeout.connect(self._drive_from_keys)
        self._key_timer.start()

    def keyPressEvent(self, e):
        self._held.add(e.key())

    def keyReleaseEvent(self, e):
        self._held.discard(e.key())
        if not self._held:
            self._cmd("stop")

    def _drive_from_keys(self):
        if not self.worker or not self._held:
            return
        if   self._held & {Qt.Key_W, Qt.Key_Up}:   self._cmd("forward")
        elif self._held & {Qt.Key_S, Qt.Key_Down}:  self._cmd("backward")
        elif self._held & {Qt.Key_A, Qt.Key_Left}:  self._cmd("left")
        elif self._held & {Qt.Key_D, Qt.Key_Right}: self._cmd("right")

    def _log(self, msg):
        self.log_view.append(msg)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar log", "spike_log.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp", "type", "action", "speed",
                "x", "y", "heading", "color1", "color2"])
            writer.writeheader()
            writer.writerows(self.log_rows)
        self._log(f"Log guardado → {path}")

    def closeEvent(self, e):
        self._disconnect()
        e.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())