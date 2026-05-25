import sys
from spike_v5 import robot, motor_pair_distancia, giroscopio, SA_posicion_relativa, calibrar, pila, stop, motor_pair_run, motor_pair_time

class RobotThread:
    def __init__(self, func, *args):
        self.func = func
        self.args = args

    def start(self):
        self.func(*self.args)

def main():
    print("LEGO Spike Prime Control Interface")
    print("Commands:")
    print("f - Forward")
    print("b - Backward")
    print("l - Turn Left")
    print("r - Turn Right")
    print("s - Stop")
    print("c - Calibrate")
    print("p - Check Battery")
    print("d - Move Distance (speed1 speed2 distance)")
    print("g - Gyro Turn (angle speed1 speed2)")
    print("sa - SA Position (angle position speed direction)")
    print("q - Quit")

    while True:
        cmd = input("Enter command: ").strip().lower()
        if cmd == 'q':
            break
        elif cmd == 'f':
            motor_pair_run(200, 200, robot)
        elif cmd == 'b':
            motor_pair_run(-200, -200, robot)
        elif cmd == 'l':
            motor_pair_run(-100, 100, robot)
        elif cmd == 'r':
            motor_pair_run(100, -100, robot)
        elif cmd == 's':
            stop(robot)
        elif cmd == 'c':
            thread = RobotThread(calibrar, robot)
            thread.start()
        elif cmd == 'p':
            thread = RobotThread(pila, robot)
            thread.start()
        elif cmd.startswith('d '):
            parts = cmd.split()
            if len(parts) == 4:
                try:
                    speed1 = int(parts[1])
                    speed2 = int(parts[2])
                    dist = int(parts[3])
                    thread = RobotThread(motor_pair_distancia, speed1, speed2, dist, robot)
                    thread.start()
                except ValueError:
                    print("Invalid numbers")
        elif cmd.startswith('g '):
            parts = cmd.split()
            if len(parts) == 4:
                try:
                    angle = int(parts[1])
                    speed1 = int(parts[2])
                    speed2 = int(parts[3])
                    thread = RobotThread(giroscopio, angle, speed1, speed2, 3, robot)
                    thread.start()
                except ValueError:
                    print("Invalid numbers")
        elif cmd.startswith('sa '):
            parts = cmd.split()
            if len(parts) == 5:
                try:
                    angle = int(parts[1])
                    pos = int(parts[2])
                    speed = int(parts[3])
                    dir = int(parts[4])
                    thread = RobotThread(SA_posicion_relativa, angle, pos, speed, dir, robot)
                    thread.start()
                except ValueError:
                    print("Invalid numbers")
        else:
            print("Unknown command")

if __name__ == '__main__':
    main()