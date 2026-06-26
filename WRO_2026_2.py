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

    con noventa grados el robot se equilibria a la perfecion para avanzar en ambos lados
    cabe recalcar que para que la garra tiene un rango de 180 grados en total
    robot.motor_central.run_angle(200, 90)
    SA_posicion_relativa_angulo_actual(200, 200, 1, robot)
    robot.motor_central.run_angle(200, -90)
    SA_posicion_relativa_angulo_actual(200, 200, 1, robot)

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
    print(f'Color sensor 1 reflection: {y}') 
    
    hola
    """

def stop(robot):
    robot.motor_izquierdo.stop()
    robot.motor_derecho.stop()

def motor_pair_reset(robot):
    robot.motor_derecho.reset_angle(0)
    robot.motor_izquierdo.reset_angle(0)

def motor_pair_distancia(velocidad, velocidad2, distancia, robot):
    robot.motor_derecho.run_angle(velocidad, distancia, wait=False)  # Motor D sin esperar
    robot.motor_izquierdo.run_angle(velocidad2, distancia + 2)
    stop(robot)

def motor_pair_distancia_cm(velocidad, velocidad2, distancia, robot):
    grados_objetivo = (distancia / 27) * 360
    if velocidad - velocidad == 0:
        robot.motor_derecho.run_angle(velocidad, grados_objetivo, wait=False)  # Motor D sin esperar
        robot.motor_izquierdo.run_angle(velocidad2 + 5, grados_objetivo)
        stop(robot)
    elif velocidad - velocidad != 0:
        robot.motor_derecho.run_angle(velocidad, grados_objetivo, wait=False)  # Motor D sin esperar
        robot.motor_izquierdo.run_angle(velocidad2, grados_objetivo)
        stop(robot)

def motor_pair_run(velocidad, velocidad2, robot):    
    robot.motor_derecho.run(velocidad)  # Motor D sin esperar
    robot.motor_izquierdo.run(velocidad2)  # Motor I sin esperar
        
def motor_pair_time(velocidad, velocidad2, tiempo, robot):
    robot.motor_derecho.run_time(velocidad, tiempo, wait=False)  # Motor D sin esperar
    robot.motor_izquierdo.run_time(velocidad2, tiempo)  # Motor I sin esperar

def motor_pair_until_stalled(velocidad, velocidad2, robot):
    robot.motor_derecho.run_until_stalled(velocidad)  # Motor D sin esperar
    robot.motor_izquierdo.run_until_stalled(velocidad2, wait=False)  # Motor I sin esperar

def motor_pair_target(velocidad, velocidad2, angulo, robot):
    motor_pair_reset(robot)
    robot.motor_derecho.run_target(velocidad, angulo, wait=False)  # Motor D sin esperar
    robot.motor_izquierdo.run_target(velocidad2, angulo)  # Motor I sin esperar

def motor_pair_dc(velocidad, velocidad2, robot):  
    robot.motor_derecho.dc(velocidad)  # Motor D sin esperar
    robot.motor_izquierdo.dc(velocidad2)  # Motor I sin esperar

def detectar_color(sensor):
    # Get the HSV data
    h, s, v = sensor.hsv()
    
    # --- 1. THE NEUTRAL CHECK (Priority) ---
    # If Saturation is low (s < 25), it's Black, Gray, or White.
    # We ignore Hue (h) entirely for these.

    if v < 20:          # Lowered threshold to catch stubborn Blacks
        return Color.BLACK, 0
    elif v > 90 and s < 5 and 0 <= h >= 180:        # High brightness
        return Color.WHITE, 300

    # --- 2. THE SPECTRUM CHECK ---
    # We only get here if Saturation (s) is high (meaning it's a "real" color)

    # Red
    if h < 20 or h > 340:
        return Color.RED, 25
    
    # Yellow
    elif h <= 68 and 5 <= s >= 10:
        return Color.YELLOW, 80
        
    # Green (Widened to catch more variants)
    elif 90 <= h <= 180:
        return Color.GREEN, 130
        
    # Blue (Only if it's actually saturated/vibrant blue)
    elif 190 <= h <= 270:
        return Color.BLUE, 230
    
    return Color.NONE, h

def error_angular(objetivo, actual):
    error = objetivo - actual

    if error > 180:
        error -= 360
    elif error < -180:
        error += 360

    return error

def giroscopio(angulo, velocidad, velocidad2, comparador, robot):

    if comparador == 1:
        while True:
            motor_pair_run(velocidad, velocidad2, robot)

            if robot.hub.imu.heading() >= angulo:
                break

            wait(10)

        stop(robot)

    elif comparador == 2:
        while True:
            motor_pair_run(velocidad, velocidad2, robot)

            if robot.hub.imu.heading() <= angulo:
                break

            wait(10)

        stop(robot)

    elif comparador == 3:
        while True:
            motor_pair_run(velocidad, velocidad2, robot)

            if abs(error_angular(angulo, robot.hub.imu.heading())) <= 3:
                break

            wait(10)

        stop(robot)

    elif comparador == 4:
        while True:
            actual = robot.hub.imu.heading()
            error = error_angular(angulo, actual)

            if abs(error) <= 5:
                break

            motor_pair_run(velocidad, velocidad2, robot)
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

    error = (angulo) - actual

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

def SA_angulo_actual(condicion, velocidad, robot):
    kp = 0.35 # empieza bajo 
    angulo = robot.hub.imu.heading() 
    if condicion: 
        robot.var += 1 
        robot.move_tank.stop() 
        return 
    actual = robot.hub.imu.heading() 
    error = angulo - actual # corregir salto entre 179 y -179 
    if error > 180: 
        error -= 360 
    elif error < -180: 
        error += 360 
    # zona muerta: si el error es muy pequeño, no corrijas 
    if abs(error) < 2: 
        error = 0 
    giro = error * kp # limitar giro para que no se vuelva loco 
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

def alineador(angulo, robot):
    if robot.hub.imu.heading() > angulo: 
        giroscopio(angulo, 30, -30, 3, robot)
    else:
        giroscopio(angulo, -30, 30, 3, robot)

def SA_color_negro(repeticiones, angulo, velocidad, sensores, robot):
    while robot.var != repeticiones: 
        if sensores == 1:
            SA(angulo, robot.color_sensor_central.color() == Color.BLACK or (robot.color_sensor_central.reflection() < 30 and robot.color_sensor_central.reflection() > 5), velocidad, robot)
        if sensores == 2: 
            SA(angulo, robot.color_sensor_izquierda.color() == Color.BLACK or (robot.color_sensor_izquierda.reflection() < 30 and robot.color_sensor_izquierda.reflection() > 5), velocidad, robot)
        if sensores == 3:
            SA(angulo, (robot.color_sensor_izquierda.color() == Color.BLACK or (robot.color_sensor_izquierda.reflection() < 30 and robot.color_sensor_izquierda.reflection() > 5)) or (robot.color_sensor_central.color() == Color.BLACK or (robot.color_sensor_central.reflection() < 30 and robot.color_sensor_central.reflection() > 5)), velocidad, robot)
    stop(robot)
    robot.var = 0

def SA_posicion_relativa_cm(distancia, angulo, velocidad, masomenos, robot):
    robot.motor_derecho.reset_angle(0)
    grados_objetivo = (distancia / 27) * 360

    while robot.var != 1:
        if masomenos == 1:
            condicion = robot.motor_derecho.angle() >= grados_objetivo
        elif masomenos == 2:
            condicion = robot.motor_derecho.angle() <= -grados_objetivo

        SA(angulo, condicion, velocidad, robot)
        wait(10)

    robot.var = 0
    stop(robot)
    wait(100)

def SA_posicion_relativa_cm_angulo_actual(distancia, velocidad, masomenos, robot):
    v = robot.hub.imu.heading()
    robot.motor_derecho.reset_angle(0)
    grados_objetivo = (distancia / 27) * 360

    while robot.var != 1:
        if masomenos == 1:
            condicion = robot.motor_derecho.angle() >= grados_objetivo
        elif masomenos == 2:
            condicion = robot.motor_derecho.angle() <= -grados_objetivo

        SA(v, condicion, velocidad, robot)
        wait(10)

    robot.var = 0
    stop(robot)
    wait(100)

def start_moving_at(velocidad_izquierda, velocidad_derecha, robot):
    robot.motor_derecho.dc(velocidad_izquierda)
    robot.motor_izquierdo.dc(velocidad_derecha)

def line_follower(MP, distance, side, robot):
    robot.motor_derecho.reset_angle(0)
    kp = 0.22
    Adegrees = 0
    degrees = distance * 27
    MotorPosA = robot.motor_derecho.angle()
    while Adegrees < degrees:
        Adegrees = abs(robot.motor_derecho.angle() - MotorPosA)
        error = robot.color_sensor_central.reflection() - 60
        PID = kp * error
        if side == 1:
            start_moving_at(MP + PID, MP - PID, robot)
        else:
            start_moving_at(MP - PID, MP + PID, robot)

def seguidor_hasta_interseccion(velocidad, robot):
    
    objetivo = 35
    negro = 25
    kp = 0.1

    while True:
        interseccion = robot.color_sensor_izquierda.reflection() < negro

        if interseccion:
            break

        lectura = robot.color_sensor_central.reflection()

        error = objetivo - lectura
        pid = kp * error

        start_moving_at(velocidad - pid, velocidad + pid, robot)

    stop(robot)

################################################################################################################################################################

def configurar():
    pila(robot)
    wait(10000)

def limpiar_llantas(robot):
    while True:
        motor_pair_run(1000, 1000, robot)

def lectura_color(robot):
    print(robot.color_sensor_central.reflection())
    print(robot.color_sensor_izquierda.reflection())

def test(robot):
    for i in range(4):
        robot.motor_central.run_target(1000, -5)
        robot.motor_central.run_target(-1000, 100)

#################################################################################################################################################################################################################################

def recoger_bloques(robot):
    if robot.color == 1:
        SA_posicion_relativa_angulo_actual(100, 250, 1, robot)
        robot.hub.imu.reset_heading(0)
        wait(100)
        robot.hub.imu.reset_heading(0)
        SA_posicion_relativa_angulo_actual(-10, -250, 2, robot)
        giroscopio(-90, 110, -165, 4, robot)
    SA_posicion_relativa_angulo_actual(120, 250, 1, robot)
    robot.hub.imu.reset_heading(0)
    wait(100)
    robot.hub.imu.reset_heading(0)
    if robot.color == 1:
        SA_posicion_relativa(40, -235, -200, 2, robot)
    if robot.color == 2:
        SA_posicion_relativa(17, -325, -200, 2, robot)
    if robot.color == 3:
        SA_posicion_relativa(17, -400, -200, 2, robot)
    if robot.color == 4:
        SA_posicion_relativa(17, -445, -200, 2, robot)
    robot.motor_bloques.run_target(1000,0)
    alineador(-1, robot)
    robot.motor_central.run_target(200, -4)
    robot.motor_bloques.run_until_stalled(-400, duty_limit=50)
    robot.motor_bloques.run(-40)
    robot.motor_bloques.stop()
    robot.motor_central.run_angle(1000, 120)


def dejar_bloques_1(robot):
    giroscopio(90, -150, 150, 4, robot)
    SA_posicion_relativa_cm(35, 120, -200, 2, robot)
    giroscopio(0, 150, -150, 4, robot)
    SA_color_negro(1, 40, -200, 1, robot)
    giroscopio(90, -160, 130, 4, robot)
    SA_posicion_relativa(89, -780, -175, 2, robot)
    dropoff_bloques(robot)
    if robot.color != 4:
        SA_posicion_relativa_angulo_actual(500, 400, 1, robot)
        giroscopio(0, 150, -150, 4, robot)
        SA_posicion_relativa(0, 550, 400, 1, robot)
        giroscopio(90, -150, 150, 4, robot)
        SA_posicion_relativa(90, 550, 400, 1, robot)
        SA_posicion_relativa_angulo_actual(-10, -250, 2, robot)
        giroscopio(0, 110, -165, 4, robot)
    else:
        SA_posicion_relativa_angulo_actual(200, 400, 1, robot)
        giroscopio(-90, 150, -150, 4, robot)


def dropoff_bloques(robot):
    robot.motor_central.run_target(300, 3)
    robot.motor_bloques.run_angle(120, 90)
    robot.motor_central.run_angle(150, 90)
    motor_pair_distancia(100, 100, 200, robot)
    '''robot.motor_central.run_target(400, 3)
    robot.motor_bloques.run_target(800, 45)
    motor_pair_distancia(-150, -150, 35, robot)
    motor_pair_distancia(100, 100, 40, robot)'''
    robot.motor_bloques.run_until_stalled(-200)
    robot.motor_central.run_until_stalled(300)

def main(robot):  
    robot.hub.imu.reset_heading(0)
    robot.color+=1
    recoger_bloques(robot)
    robot.color +=1
    dejar_bloques_1(robot)
    recoger_bloques(robot)
    robot.color += 1
    dejar_bloques_1(robot)
    recoger_bloques(robot)
    robot.color += 1
    dejar_bloques_1
    recoger_bloques(robot)
    robot.color +=1
    dejar_bloques_1(robot)

robot.hub.imu.reset_heading(0)
wait(500)
main(robot)