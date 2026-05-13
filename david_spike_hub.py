from pybricks.hubs import PrimeHub
from pybricks.robotics import DriveBase
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Color, Stop, Direction
from pybricks.tools import wait
from usys import stdin, stdout
import ujson
import umath as math
import _thread

# ── Hardware ──────────────────────────────────────────────────────
hub      = PrimeHub()
motor_mf = Motor(Port.F)
motor_mb = Motor(Port.B, positive_direction=Direction.COUNTERCLOCKWISE)
motor_lc = Motor(Port.D)
color1   = ColorSensor(Port.E)
color2   = ColorSensor(Port.A)

drive = DriveBase(motor_mf, motor_mb, wheel_diameter=86, axle_track=120)
drive.settings(straight_speed=300, straight_acceleration=400,
               turn_rate=150,      turn_acceleration=300)

# ── Helpers ───────────────────────────────────────────────────────
COLOR_MAP = {
    Color.BLACK:  "BLACK",  Color.WHITE:  "WHITE",
    Color.RED:    "RED",    Color.GREEN:  "GREEN",
    Color.BLUE:   "BLUE",   Color.YELLOW: "YELLOW",
    Color.NONE:   "NONE",
}

def color_name(sensor):
    return COLOR_MAP.get(sensor.color(), "UNKNOWN")

def _safe(fn, default):
    try:
        return fn()
    except:
        return default

def telemetry():
    dist    = _safe(lambda: drive.distance(), 0)
    heading = _safe(lambda: hub.imu.heading(), 0)
    rad     = math.radians(heading)
    return {
        "x":       round(dist * math.sin(rad), 1),
        "y":       round(dist * math.cos(rad), 1),
        "heading": round(heading, 1),
        "dist":    round(dist, 1),
        "battery": _safe(lambda: max(0, min(100, int((hub.battery.voltage() - 7000) / 13))), -1),
        "color1":  _safe(lambda: COLOR_MAP.get(color1.color(), "UNKNOWN"), "ERR"),
        "color2":  _safe(lambda: COLOR_MAP.get(color2.color(), "UNKNOWN"), "ERR"),
        "ref1":    _safe(lambda: color1.reflection(), -1),
        "ref2":    _safe(lambda: color2.reflection(), -1),
    }

def send(data):
    stdout.write(ujson.dumps(data) + "\n")

# ── Command dispatcher ────────────────────────────────────────────
def dispatch(cmd):
    action = cmd.get("cmd", "")
    speed  = int(cmd.get("speed", 300))
    angle  = int(cmd.get("angle", 350))

    if   action == "forward":   drive.drive(speed, 0)
    elif action == "backward":  drive.drive(-speed, 0)
    elif action == "left":      drive.drive(0, -speed)
    elif action == "right":     drive.drive(0,  speed)
    elif action == "stop":      drive.stop()
    elif action == "arm_up":    motor_lc.run_angle(200, -abs(angle))
    elif action == "arm_down":  motor_lc.run_angle(200,  abs(angle))
    elif action == "reset_pos":
        drive.reset()
        hub.imu.reset_heading(0)

# ── Stdin reader thread ───────────────────────────────────────────
# uselect.poll does NOT work with BLE stdin in Pybricks.
# Blocking stdin.read(1) in a separate thread is the only reliable approach.
_cmd_queue = []
_lock      = _thread.allocate_lock()

def _stdin_reader():
    buf = ""
    while True:
        try:
            ch = stdin.read(1)
            if not ch:
                continue
            if isinstance(ch, (bytes, bytearray)):
                ch = ch.decode("utf-8", "ignore")
            if ch == "\n":
                line = buf.strip()
                buf  = ""
                if line:
                    _lock.acquire()
                    _cmd_queue.append(line)
                    _lock.release()
            else:
                buf += ch
        except Exception:
            pass

_thread.start_new_thread(_stdin_reader, ())

# ── Main loop ─────────────────────────────────────────────────────
hub.light.on(Color.GREEN)
send({"msg": "SPIKE ready"})

while True:
    # Drain any commands received by the reader thread
    _lock.acquire()
    pending = list(_cmd_queue)
    _cmd_queue.clear()
    _lock.release()

    for line in pending:
        try:
            dispatch(ujson.loads(line))
        except Exception as e:
            send({"error": str(e)})

    try:
        send(telemetry())
    except Exception:
        pass
    wait(50)
