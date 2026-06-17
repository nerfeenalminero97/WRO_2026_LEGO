from pybricks.hubs import PrimeHub
from pybricks.pupdevices import ColorSensor
from pybricks.parameters import Port, Color
from pybricks.tools import wait

hub    = PrimeHub()
sensor = ColorSensor(Port.F)

# Sin esto, el sensor no busca negro y clasifica todo como blanco
sensor.detectable_colors([Color.BLACK, Color.WHITE, Color.RED,
                          Color.GREEN, Color.BLUE, Color.YELLOW])

while True:
    hsv = sensor.hsv()
    print("color:{:<10} reflejo:{:>3}  h:{:>3} s:{:>3} v:{:>3}".format(
        str(sensor.color()), sensor.reflection(), hsv.h, hsv.s, hsv.v
    ))
    wait(300)
