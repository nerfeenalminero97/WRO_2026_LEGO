from pybricks.hubs import PrimeHub
from pybricks.robotics import DriveBase
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Color, Stop, Direction
from pybricks.tools import wait
 
class Robot: 
    def __init__(self):
        self.hub = PrimeHub()

        self.motor_mf = Motor(Port.F)
        self.motor_mb = Motor(Port.D, positive_direction=Direction.COUNTERCLOCKWISE)
        self.motor_ga = Motor(Port.A)
        self.motor_le = Motor(Port.E, positive_direction=Direction.COUNTERCLOCKWISE)

        self.motor_color = Motor(Port.C)
        self.color_sensor = ColorSensor(Port.B)

        self.lista_colores = []
        self.color = 0
        self.dicc_colores = {}
        self.var = 0
        self.PRIORIDAD_COLORES = [Color.YELLOW, Color.BLUE, Color.GREEN, Color.WHITE]
        self.MAX_BLOQUES_POR_COLOR = 6
        self.BLOQUES_POR_GRUPO = 4

        self.move_tank = DriveBase(
            self.motor_mf,
            self.motor_mb,
            wheel_diameter=86,
            axle_track=120
        )

robot = Robot()

# Wait for IMU to be ready (optional, remove if causing issues)
while not robot.hub.imu.ready():
    wait(10)

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
    motor_mc.run_angle(1000, -100)  # Motor C espera (sincroniza ambos)
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
    motor_mc.run_target(100, 360)

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
    robot.motor_mb.stop()
    robot.motor_mf.stop()

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
            SA(angulo, robot.color_sensor.color() == Color.BLACK or (robot.color_sensor.reflection() < 30 and robot.color_sensor.reflection() > 5), velocidad, robot)
    stop(robot)
    robot.var = 0

def configurar():
    pila(robot)
    wait(10000)

def SA_posicion_relativa_cm(distancia, angulo, velocidad, masomenos, robot):
    robot.motor_mf.reset_angle(0)
    grados_objetivo = (distancia / 27) * 360

    while robot.var != 1:
        if masomenos == 1:
            condicion = robot.motor_mf.angle() >= grados_objetivo
        elif masomenos == 2:
            condicion = robot.motor_mf.angle() <= -grados_objetivo

        SA(angulo, condicion, velocidad, robot)
        wait(10)

    robot.var = 0
    stop(robot)
    wait(100)

def SA_posicion_relativa_cm_angulo_actual(distancia, velocidad, masomenos, robot):
    v = robot.hub.imu.heading()
    robot.motor_mf.reset_angle(0)
    grados_objetivo = (distancia / 27) * 360

    while robot.var != 1:
        if masomenos == 1:
            condicion = robot.motor_mf.angle() >= grados_objetivo
        elif masomenos == 2:
            condicion = robot.motor_mf.angle() <= -grados_objetivo

        SA(v, condicion, velocidad, robot)
        wait(10)

    robot.var = 0
    stop(robot)
    wait(100)

##############################################################################################################
##############################################################################################################

def recoger_lapiz(robot):
    robot.motor_ga.run_angle(200, 210)
    wait(6000)
    robot.motor_ga.run_angle(200, -210)

def limpiar_llantas(robot):
    while True:
        motor_pair_run(1000, 1000, robot)

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
    SA_posicion_relativa_angulo_actual(1080, 200, 1, robot)

#################################################################################################################################################################################################################################
##################################################################################################################################################################################################################################

def computadora_capa_interna(robot):
    SA_posicion_relativa(0, -100, -90, 2, robot)
    SA_posicion_relativa(0, 10, 90, 1, robot)
    robot.motor_le.run_angle(200, -60)
    robot.motor_le.run_angle(200, 60)
    robot.motor_le.run_angle(200, -60)
    wait(1000)
    robot.motor_ga.run_angle(200, -210)
    robot.motor_le.run_angle(200, 55)
    robot.motor_ga.run_angle(200, 150)

def computadora_base_relieve(robot):
    robot.hub.imu.reset_heading(0)
    robot.motor_color.run_angle(1000, 340)
    SA_posicion_relativa_angulo_actual(100, 200, 1, robot)
    motor_pair_distancia(300, 300, 20, robot)
    wait(500)
    robot.hub.imu.reset_heading(0)
    SA_posicion_relativa(3, -1200, -320, 2, robot)
    giroscopio(-35, 150, -150, 2, robot)
    motor_pair_distancia(300, 300, 100, robot)
    giroscopio(0, -150, 0, 1, robot)
    SA_posicion_relativa(0, 350, 300, 1, robot)
    motor_pair_distancia(-300,-300, 50, robot)
    giroscopio(-175, 150, -100, 2, robot)
    SA_posicion_relativa(0, 500, 300, 1, robot)
    robot.motor_mf.run_angle(300, 225)
    robot.motor_mb.run_angle(300, 200)
    SA_posicion_relativa_cm(20, 0, 300, 1, robot)
    motor_pair_distancia(150, -150, 185, robot)
    motor_pair_distancia(-300, 300, 185, robot)

    #checar doble vuelta

def mouse_teclas(robot):
    SA_posicion_relativa_cm(50, 0, 300, 1, robot)
    robot.motor_ga.run_angle(1000, -235)
    SA_posicion_relativa(0, 20, 150, 1, robot)
    robot.motor_ga.run_angle(1000, -80)
    wait(100)
    SA_posicion_relativa(0, -60, -300, 2, robot)
    giroscopio(39, 150, -150, 4, robot)
    SA_posicion_relativa(39, 900, 400, 1, robot)
    robot.motor_color.run_angle(1000, -500)
    SA_posicion_relativa(39, 100, 150, 1, robot)
    giroscopio(0, 120, 15, 4, robot)
    SA_posicion_relativa_angulo_actual(150, 200, 1, robot)
    #Corregir SA
    #asegurar que la garra este bien recta para la rotacion
    #checar el giro paa que deje los escombros en lugar

def computadora_primer_plano_pantalla(robot):
    giroscopio(0, 10, 150, 1, robot)
    SA_posicion_relativa_cm(147, 0, 300, 1, robot)
    SA_posicion_relativa(0, -250, -400, 2, robot)
    giroscopio(90, -150, 150, 1, robot)
    SA_posicion_relativa(90, -50, -300, 2, robot)

def letras(robot):
    robot.motor_ga.run_angle(300, -100)
    robot.motor_le.run_angle(300, -60)

def pantalla_real(robot):
    SA_posicion_relativa(0, 100, 250, 1, robot)
    giroscopio(-90, -150, 150, 2, robot)
    SA_posicion_relativa(-90, 50, 300, 1, robot)
    giroscopio(-175, -150, 150, 2, robot)
    SA_posicion_relativa(0, -700, -300, 2, robot)
    giroscopio(0, 150, 50, 2, robot)
    SA_posicion_relativa(0, 400, 300, 1, robot)

def computadora_releive_pantalla(robot):
    SA_posicion_relativa_cm(-92, 37, -200, 2, robot)
    giroscopio(175, -150, 150, 1, robot)
    SA_posicion_relativa(0, 75, 150, 1, robot)
    robot.motor_ga.run_angle(300, -235)
    SA_posicion_relativa(0, 50, 250, 1, robot)
    robot.motor_ga.run_angle(300, -75)
    wait(100)
    SA_posicion_relativa(0, -150, -300, 2, robot)

def main(robot):
    computadora_capa_interna(robot)
    computadora_base_relieve(robot)
    mouse_teclas(robot)
    computadora_primer_plano_pantalla(robot)
    computadora_releive_pantalla(robot)
    pantalla_real(robot)
    letras(robot)

main(robot)