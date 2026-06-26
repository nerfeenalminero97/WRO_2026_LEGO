from pybricks.hubs import PrimeHub
from pybricks.robotics import DriveBase
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Color, Stop, Direction
from pybricks.tools import wait
 
class Robot: 
    def __init__(self):
        self.hub = PrimeHub()

        self.motor_derecho = Motor(Port.F)
        self.motor_izquierdo = Motor(Port.D, positive_direction=Direction.COUNTERCLOCKWISE)
        self.motor_central = Motor(Port.B)
        self.motor_bloques = Motor(Port.A, positive_direction=Direction.COUNTERCLOCKWISE)

        self.color_sensor_central = ColorSensor(Port.E)
        self.color_sensor_izquierda = ColorSensor(Port.C)

        self.lista_colores_central = []
        self.lista_colores_izquierdo = []
        self.color = 0
        self.dicc_colores = {}
        self.var = 0
        self.PRIORIDAD_COLORES = [Color.YELLOW, Color.BLUE, Color.GREEN, Color.WHITE]
        self.MAX_BLOQUES_POR_COLOR = 6
        self.BLOQUES_POR_GRUPO = 4

        self.move_tank = DriveBase(
            self.motor_derecho,
            self.motor_izquierdo,
            wheel_diameter=86,
            axle_track=120
        )

robot = Robot()

# Wait for IMU to be ready (optional, remove if causing issues)
# while not robot.hub.imu.ready():
#     wait(10)

def pila(robot):
    voltaje = robot.hub.battery.voltage()

    # Mostrar número en pantalla
    robot.hub.display.number(voltaje)

    # Indicador con luz
    if voltaje > 8000:
        robot.hub.light.on(Color.GREEN)   # batería alta
    elif voltaje > 7000:
        robot.hub.light.on(Color.YELLOW)  # batería media
    else:
        robot.hub.light.on(Color.RED)  
    porcentaje = int((voltaje - 7000) / 13)
    print(f'{porcentaje}% de pila')
    print(f'Voltaje = {voltaje}')
  
"""def notas():
    #Motor_MF = Motor mediano puerto F
    #Motor_MB = Motor mediano puerto B
    #Motor_GC = Motor grande puerto C
    #Motor_GD = Motor grande puerto D
    # Ejecutar ambos motores de forma sincronizada (en paralelo) por distanica, segundo argumento es la distancia, primer argumento velocidad
    motor_mf.run_angle(-1000, 100, wait=False)  # Motor F sin esperar
    motor_mb.run_angle(1000, -100)  # Motor B espera (sincroniza ambos)
    wait(1000)

    #obtener angulo del motor 
    y = motor_mf.angle()
    print(y)

    #para el motor sin esperar a que termine la acción
    motor_mf.brake()

    motor_mf.reset_angle(0)  # Reiniciar el ángulo del motor a 0, con none como argumento

    #de esta manera funciona el comando run sin esperar a que termine la acción, el motor se detiene con el comando stop
    motor_mf.run(1000)
    wait(1000)
    motor_mf.stop()

    #devuelve True si el motor ha terminado su acción, False si no ha terminado
    motor_mf.run_angle(100, 100, wait=False)
    y = motor_mf.done()
    print (y)

    #avanza hasta que el motor alcance un ángulo específico, en este caso 360 grados, sin esperar a que termine la acción, segundo arugmento es el angulo que deaseamos llegar
    motor_mf.run_target(100, 360, wait=False)
    motor_mb.run_target(100, 360)

    motor_mf.close()  # Cierra el motor, liberando recursos. No se puede usar el motor después de cerrarlo a menos que se vuelva a crear una instancia del motor.

    #Motor se mueve por tiempo, primer argumento es la potencia, segundo argumento es el tiempo en milisegundos, tercer argumento es si espera a que termine la acción o no
    motor_mf.run_time(1000, 2000, wait=True)

    # El motor se mueve hasta que se detiene por una fuerza externa, primer argumento es la potencia, segundo argumento es el tipo de detención (en este caso, detenerse cuando se encuentra con una resistencia)
    motor_mf.run_until_stalled(100)

    #Configurar el maximo voltaje que se le puede dar al motor en el programa, 0-100
    motor_mf.settings(100)

    #lee a que velocidad se esta moviendo el motor en ese momento, devuelve un valor positivo si se mueve hacia adelante, negativo si se mueve hacia atrás, y 0 si esta detenido
    motor_mf.speed(100)

    #similar a speed, checa si esta trabado el motor, devuelve True si esta trabado, False si no lo esta
    motor_mf.stalled()

    #se mueve a maxima velocidad hacia el angulo del motor deseado
    motor_mf.track_target(100)

    hub.imu.tilt()#obtiene el pich roll y los angulos del robot
    hub.imu.ready()#checa si esta calibrado el dispositivo
    v = hub.imu.stationary()# checa si el robot esta en movimiento o quieto

    #Se va recto el robot 
    robot.move_tank.straight(90)
    wait(1000)
    robot.move_tank.stop()

    c = robot.color_sensor2.reflection()
    print(c)
    wait (200000)

    #maneja a base de potencia, no de velocidad, el valor va de -100 a 100
    while True:
        motor_mf.dc(100)
        
        # de esta manera avanza infinitamente con la velocidad
        while True:
            motor_mf.run(100) 

def calibrar(robot):
    c = robot.color_sensor2.reflection()
    y = robot.color_sensor1.reflection()
    print(f'Color sensor 2 reflection: {c}')
    print(f'Color sensor 1 reflection: {y}') """

def stop(robot):
    robot.motor_derecho.stop()
    robot.motor_izquierdo.stop()

def motor_pair_reset(robot):
    robot.motor_mf.reset_angle(0)
    robot.motor_mb.reset_angle(0)

def motor_pair_distancia(velocidad, velocidad2, distancia, robot):
    robot.motor_mf.run_angle(velocidad, distancia, wait=False)  # Motor F sin esperar
    robot.motor_mb.run_angle(velocidad2, distancia)
    stop(robot)

def motor_pair_run(velocidad, velocidad2, robot):    
    robot.motor_mf.run(velocidad)  # Motor F sin esperar
    robot.motor_mb.run(velocidad2)  # Motor B sin esperar
        
def motor_pair_time(velocidad, velocidad2, tiempo, robot):
    robot.motor_mf.run_time(velocidad, tiempo, wait=False)  # Motor F sin esperar
    robot.motor_mb.run_time(velocidad2, tiempo)  # Motor B sin esperar

def motor_pair_until_stalled(velocidad, velocidad2, robot):
    robot.motor_mf.run_until_stalled(velocidad)  # Motor F sin esperar
    robot.motor_mb.run_until_stalled(velocidad2, wait=False)  # Motor B sin esperar

def motor_pair_target(velocidad, velocidad2, angulo, robot):
    motor_pair_reset(robot)
    robot.motor_mf.run_target(velocidad, angulo, wait=False)  # Motor F sin esperar
    robot.motor_mb.run_target(velocidad2, angulo)  # Motor B sin esperar

def motor_pair_dc(velocidad, velocidad2, robot):  
    robot.motor_mf.dc(velocidad)  # Motor F sin esperar
    robot.motor_mb.dc(velocidad2)  # Motor B sin esperar

def giroscopio(angulo, velocidad, velocidad2, comparador, robot):  
    if comparador == 1:  
        while True:
            motor_pair_run(velocidad, velocidad2, robot)

            if robot.hub.imu.heading() >= angulo:
                break

        stop(robot)

    if comparador == 2:  
        while True:
            motor_pair_run(velocidad, velocidad2, robot)

            if robot.hub.imu.heading() <= angulo:
                break

        stop(robot)

    if comparador == 3:  
        while True:
            motor_pair_run(velocidad, velocidad2, robot)

            if abs(robot.hub.imu.heading()) == angulo:
                break

    if comparador == 4:

        rango_max = angulo + 5
        rango_min = angulo - 5

        while True:

            motor_pair_run(velocidad, velocidad2, robot)

            actual = robot.hub.imu.heading()

            if rango_min <= actual and actual <= rango_max:
                break

            wait(10)

        stop(robot)

def limitar(valor, minimo, maximo):
    if valor < minimo:
        return minimo
    if valor > maximo:
        return maximo
    return valor

def SA(angulo, condicion, velocidad, robot):
    kp = 0.4  # empieza bajo

    if condicion:
        robot.var += 1
        robot.move_tank.stop()
        return

    actual = robot.hub.imu.heading()

    error = angulo - actual

    # corregir salto entre 179 y -179
    if error > 180:
        error -= 360
    elif error < -180:
        error += 360

    # zona muerta: si el error es muy pequeño, no corrijas
    if abs(error) < 2:
        error = 0

    giro = error * kp

    # limitar giro para que no se vuelva loco
    giro = limitar(giro, -30, 30)

    robot.move_tank.drive(velocidad, giro)

def SA_posicion_relativa(angulo, posicion_relativa, velocidad, masomenos, robot):
    robot.motor_derecho.reset_angle(0)

    while robot.var != 1:
        if masomenos == 1:
            condicion = robot.motor_derecho.angle() >= posicion_relativa
        elif masomenos == 2:
            condicion = robot.motor_derecho.angle() <= posicion_relativa

        SA(angulo, condicion, velocidad, robot)
        wait(10)

    robot.var = 0
    stop(robot)
    wait(100)
    
def SA_posicion_relativa_angulo_actual(posicion_relativa, velocidad, masomenos, robot):
    angulo = robot.hub.imu.heading()
    robot.motor_mf.reset_angle(0)

    while robot.var != 1:
        if masomenos == 1:
            condicion = robot.motor_mf.angle() >= posicion_relativa
        elif masomenos == 2:
            condicion = robot.motor_mf.angle() <= posicion_relativa

        SA(angulo, condicion, velocidad, robot)
        wait(10)

    robot.var = 0
    stop(robot)
    wait(100)

def alineador(angulo, robot):
    if robot.hub.imu.heading() > angulo: 
        giroscopio(angulo, -20, 20, 3)
    else:
        giroscopio(angulo, 20, -20, 3)
    
def SA_color_negro(repeticiones, angulo, velocidad, sensores, robot):
    while robot.var != repeticiones: 
        if sensores == 1:
            SA(angulo, robot.color_sensor1.color() == Color.BLACK or (robot.color_sensor1.reflection() < 30 and robot.color_sensor1.reflection() > 5), velocidad, robot)
        elif sensores == 2:
            SA(angulo, robot.color_sensor2.color() == Color.BLACK or (robot.color_sensor2.reflection() < 30 and robot.color_sensor2.reflection() > 5), velocidad, robot)
        elif sensores == 3: 
            SA(angulo, (robot.color_sensor1.color() == Color.BLACK and robot.color_sensor2.color() == Color.BLACK) or ((robot.color_sensor1.reflection() < 30 and robot.color_sensor1.reflection() > 5) and (robot.color_sensor2.reflection() < 30 and robot.color_sensor2.reflection() > 5)), velocidad, robot)
    stop(robot)
    robot.var = 0

def configurar():
    pila(robot)
    wait(10000)

def recoger_bloques(robot):
    robot.motor_gd.run_angle(200, 60)
    robot.motor_gd.run_angle(200, -60)
    robot.motor_gd.run_angle(200, 60)
    wait(1000)
    robot.motor_lc.run_angle(200, -210)
    robot.motor_gd.run_angle(200, -55)
    robot.motor_lc.run_angle(200, 250)
    stop(robot)

def limpiar_llantas(robot):
    while True:
        motor_pair_run(1000, 1000, robot)

def construccion_pala1_bloque0cemento(robot):
    robot.hub.imu.reset_heading(0)
    robot.motor_mb.run_angle(300, 60)
    giroscopio(0, 100, -10, 1, robot)
    motor_pair_distancia(300, 300, 80, robot)
    wait(500)
    robot.hub.imu.reset_heading(0)
    SA_posicion_relativa(0, -600, -320, 2, robot)
    SA_color_negro(1, -1, -320, 2, robot)
    SA_posicion_relativa(1, -200, -300, 2, robot)
    giroscopio(-35, 150, -150, 2, robot)
    motor_pair_distancia(300, 300, 100, robot)
    giroscopio(0, -150, 0, 1, robot)
    SA_posicion_relativa(0, 350, 300, 1, robot)
    motor_pair_distancia(-300,-300, 50, robot)
    giroscopio(-175, 150, -100, 2, robot)
    SA_posicion_relativa(0, 575, 300, 1, robot)
    robot.motor_mf.run_angle(100, 100)
    SA_posicion_relativa_angulo_actual(300, 280, 1, robot)
    robot.motor_mf.run_angle(200, 270)
    #deja bloque de cemento
    SA_posicion_relativa(90, -100, -400, 2, robot)
    giroscopio(170, -130, 130, 1, robot)
    motor_pair_distancia(-100, 100, 20, robot)
    #corroborarse que funciona igual con la grua puesta
    #mejorar y checar SA
    #checar doble vuelta

def test(robot):
    while False:
        motor_pair_distancia(220, 200, 75, robot)
        wait(500)
        robot.hub.imu.reset_heading(0)
        SA_posicion_relativa(0, -100, -200, 2, robot)
        giroscopio(-175, 100, -100, 2, robot)
        wait(1000)
        robot.motor_mf.run_angle(100, 100)
        SA_posicion_relativa(160, 100, 200, 1, robot)
    SA_posicion_relativa_angulo_actual(-100, -100, 2, robot)
    robot.hub.imu.reset_heading(0)
    SA_posicion_relativa(0, 720, 200, 1, robot)

def escombros_blancos(robot):
    SA_posicion_relativa(0, 450, 500, 1, robot)
    SA_posicion_relativa(0, 100, 500, 1, robot)
    robot.motor_lc.run_angle(300, 235)
    SA_posicion_relativa(0, 50, 250, 1, robot)
    robot.motor_lc.run_angle(300, 70)
    wait(100)
    SA_posicion_relativa(0, -160, -300, 2, robot)
    giroscopio(27, 120, 20, 2, robot)
    SA_posicion_relativa(30, 1100, 600, 1, robot)
    #SA_posicion_relativa_angulo_actual(1100, 700, 1, robot)
    robot.motor_lc.run_angle(300, -295)
    SA_posicion_relativa_angulo_actual(-150, -300, 2, robot)
    robot.motor_lc.run_angle(300, 295)
    SA_posicion_relativa_angulo_actual(150, 300, 1, robot)
    SA_posicion_relativa_angulo_actual(-260, -300, 2, robot)
    #Corregir SA
    #asegurar que la garra este bien recta para la rotacion
    #checar el giro paa que deje los escombros en lugar

def leer_color(robot):
    giroscopio(0, 100, -100, 1, robot)


#configurar()
#limpiar_llantas(robot)
#test(robot)
def main():
    robot.hub.imu.reset_heading(0)
    SA_posicion_relativa(0, 1000, 200, 1, robot)

main()