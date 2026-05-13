from pybricks.hubs import PrimeHub
from pybricks.robotics import DriveBase
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Color, Stop, Direction
from pybricks.tools import wait
from usys import stdin, stdout
import ujson
import umath as math
import uselect

# ── Hardware (same ports as your original code) ──────────────────
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

def battery_pct():
    v = hub.battery.voltage()
    return max(0, min(100, int((v - 7000) / 13)))

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

# ── Main loop ─────────────────────────────────────────────────────
_poll = uselect.poll()
_poll.register(stdin, uselect.POLLIN)

hub.light.on(Color.GREEN)
send({"msg": "SPIKE ready"})

buf  = ""
tick = 0
while True:
    tick += 1

    # poll(40) blocks up to 40 ms — gives BLE stack time to deliver data
    # poll(0) misses BLE stdin because the firmware queues it asynchronously
    try:
        events = _poll.poll(40)
    except Exception as pe:
        send({"poll_err": str(pe)})
        events = []

    if events:
        send({"poll_fired": tick})          # confirms poll ever detects stdin
        try:
            ch = stdin.read(1)
        except OSError as oe:
            ch = None
            send({"read_err": str(oe)})

        while ch:
            if isinstance(ch, (bytes, bytearray)):
                ch = ch.decode("utf-8", "ignore")
            if ch == "\n":
                line = buf.strip()
                buf  = ""
                if line:
                    send({"debug_recv": line})
                    try:
                        dispatch(ujson.loads(line))
                        send({"debug_dispatched": True})
                    except Exception as e:
                        send({"error": str(e), "raw": line})
            else:
                buf += ch
            # try to grab next char without waiting
            try:
                ch = stdin.read(1) if _poll.poll(0) else None
            except OSError:
                ch = None

    # heartbeat every ~2 s so we know hub is alive
    if tick % 40 == 0:
        send({"alive": tick})

    try:
        send(telemetry())
    except Exception:
        pass
    wait(10)    # shorter wait so we don't miss fast bursts