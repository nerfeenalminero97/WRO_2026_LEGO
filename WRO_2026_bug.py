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

        self.lista_colores = []
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
    robot.motor_izquierdo.run_angle(velocidad2, distancia)
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

def color(robot):
    # Get the HSV data
    h, s, v = robot.color_sensor.hsv()
        
    # --- 1. THE NEUTRAL CHECK (Priority) ---
    # If Saturation is low (s < 25), it's Black, Gray, or White.
    # We ignore Hue (h) entirely for these.
    
    if s < 25: 
        if v < 20:          # Lowered threshold to catch stubborn Blacks
            return "Black", 0
        elif v > 70:        # High brightness
            return "White", 300
        else:               # Anything in between with low saturation
            return "Black", 150

    # --- 2. THE SPECTRUM CHECK ---
    # We only get here if Saturation (s) is high (meaning it's a "real" color)

    # Red
    if h < 20 or h > 340:
        return "Red", 25
        
    # Yellow
    elif 40 <= h <= 85:
        return "Yellow", 80
            
    # Green (Widened to catch more variants)
    elif 90 <= h <= 180:
        return "Green", 130
            
    # Blue (Only if it's actually saturated/vibrant blue)
    elif 190 <= h <= 270:
        return "Blue", 230
        
    return "Unknown", 

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
        giroscopio(angulo, -20, 20, 4, robot)
    else:
        giroscopio(angulo, 20, -20, 4, robot)

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

def seguidor_linea_negra(robot):
    #no funciona un culo
    velocidad_base = 200
    kp = 4

    # Ajusta este valor según tus lecturas
    objetivo = 57  

    while True:
        luz = robot.color_sensor_central.reflection()

        error = objetivo - luz
        correccion = kp * error

        velocidad_izq = velocidad_base - correccion
        velocidad_der = velocidad_base + correccion

        motor_pair_run(velocidad_der, velocidad_izq, robot)

        wait(10)

################################################################################################################################################################

def configurar():
    pila(robot)
    wait(10000)

def limpiar_llantas(robot):
    while True:
        motor_pair_run(1000, 1000, robot)

def test(robot):
    SA_posicion_relativa_cm_angulo_actual(27,-300, 2, robot)

#################################################################################################################################################################################################################################

def recoger_bloques(robot):
    SA_posicion_relativa(0, -100, -90, 2, robot)
    SA_posicion_relativa(0, 10, 90, 1, robot)
    robot.motor_le.run_angle(200, -60)
    robot.motor_le.run_angle(200, 60)
    robot.motor_le.run_angle(200, -60)
    wait(1000)
    robot.motor_ga.run_angle(200, -210)
    robot.motor_le.run_angle(200, 55)
    robot.motor_ga.run_angle(200, 150)

def construccion_pala1_bloque0cemento(robot):
    robot.motor_central.run_angle(200, -90)
    robot.motor_central.run_angle(200, 90)
    robot.hub.imu.reset_heading(0)
    SA_posicion_relativa_angulo_actual(-100, -700, 2, robot)
    wait(500)
    robot.hub.imu.reset_heading(0)
    SA_posicion_relativa_cm(53, 0, 300, 1, robot)
    robot.motor_central.run_angle(800, -100)
    SA_posicion_relativa_cm(25, 0, -300, 2, robot)
    robot.motor_central.run_angle(800, 100)
    robot.motor_derecho.run_angle(300, 180)
    robot.motor_izquierdo.run_angle(300, 180)
    SA_posicion_relativa_cm(40, 0, 400, 1, robot)
    robot.motor_izquierdo.run_angle(300, 180)
    robot.motor_derecho.run_angle(300, 180)
    robot.motor_central.run_angle(800, -100)
    robot.motor_derecho.run_angle(300, 180)
    robot.motor_izquierdo.run_angle(300, 180)
    

    '''giroscopio(-35, 150, -150, 2, robot)
    motor_pair_distancia(300, 300, 100, robot)
    giroscopio(0, -150, 0, 1, robot)
    SA_posicion_relativa(0, 350, 300, 1, robot)
    motor_pair_distancia(-300,-300, 50, robot)
    giroscopio(-175, 255, -150, 2, robot)
    SA_posicion_relativa(0, 500, 300, 1, robot)
    robot.motor_derecho.run_angle(300, 235)
    robot.motor_izquierdo.run_angle(300, 210)
    SA_posicion_relativa_cm(20, 0, 300, 1, robot)
    motor_pair_distancia(150, -150, 185, robot)
    motor_pair_distancia(-300, 300, 185, robot)
    #checar doble vuelta'''

def escombros_blancos(robot):
    SA_posicion_relativa_cm(50, 0, 300, 1, robot)
    robot.motor_ga.run_angle(1000, -235)
    SA_posicion_relativa(0, 20, 150, 1, robot)
    robot.motor_ga.run_angle(1000, -80)
    wait(100)
    SA_posicion_relativa(0, -60, -300, 2, robot)
    giroscopio(42, 150, -150, 4, robot)
    SA_posicion_relativa(42, 900, 400, 1, robot)
    robot.motor_color.run_angle(1000, -500)
    SA_posicion_relativa(43, 300, 150, 1, robot)
    giroscopio(0, 120, 15, 4, robot)
    alineador(0, robot)
    SA_posicion_relativa_angulo_actual(170, 200, 1, robot)
    #Corregir SA
    #asegurar que la garra este bien recta para la rotacion
    #checar el giro paa que deje los escombros en lugar<

def leer_color(robot):
    #robot.motor_color.run_angle(1000, -220)
    robot.color = color(robot)
    robot.lista_colores.append(robot.color)
    robot.color = 0 
    for i in range(3):
        robot.color = color(robot)
        robot.lista_colores.append(robot.color)
        SA_posicion_relativa(0, -45, -200, 2, robot)
        robot.color = 0 
    robot.motor_color.run_angle(1000, -490)
    robot.color = color(robot)
    robot.lista_colores.append(robot.color)
    robot.color = 0 
    for i in range(3):
        robot.color = color(robot)
        robot.lista_colores.append(robot.color)
        SA_posicion_relativa(0, 45, 200, 1, robot)
        robot.color = 0 
    robot.motor_color.run_angle(1000, -490)
    giroscopio(175, -100, 100, 2, robot)
    robot.color = color(robot)
    robot.lista_colores.append(robot.color)
    robot.color = 0 
    for i in range(3):
        robot.color = color(robot)
        robot.lista_colores.append(robot.color)
        SA_posicion_relativa(0, -45, -200, 2, robot)
        robot.color = 0 
    robot.motor_color.run_angle(1000, 1260)
    robot.motor_ga.run_angle(1000, 235)
    SA_posicion_relativa(0, -100, -200, 2, robot)
    giroscopio(45, -120, 120, 4, robot)

def puntos_grupo(grupo, color):
    correctos = 0

    for c in grupo:
        if c == color:
            correctos += 1

    incorrectos = robot.BLOQUES_POR_GRUPO - correctos
    return correctos * 10 + incorrectos * 5

def prioridad_asignacion(asignacion):
    total = 0

    for color in asignacion:
        total += robot.PRIORIDAD_COLORES.index(color)

    return total

def asignacion_valida(asignacion):
    uso = {}

    for color in asignacion:
        if color in uso:
            uso[color] += robot.BLOQUES_POR_GRUPO
        else:
            uso[color] = robot.BLOQUES_POR_GRUPO

    for color in uso:
        if uso[color] > robot.MAX_BLOQUES_POR_COLOR:
            return False

    return True

def elegir_mejor_asignacion(grupos):
    mejor_asignacion = None
    mejor_puntaje = -1
    mejor_prioridad = 999

    for color1 in robot.PRIORIDAD_COLORES:
        for color2 in robot.PRIORIDAD_COLORES:
            for color3 in robot.PRIORIDAD_COLORES:

                asignacion = [color1, color2, color3]

                if not asignacion_valida(asignacion):
                    continue

                puntaje = (
                    puntos_grupo(grupos[0], color1) +
                    puntos_grupo(grupos[1], color2) +
                    puntos_grupo(grupos[2], color3)
                )

                prioridad = prioridad_asignacion(asignacion)

                if puntaje > mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor_asignacion = asignacion
                    mejor_prioridad = prioridad

                elif puntaje == mejor_puntaje and prioridad < mejor_prioridad:
                    mejor_asignacion = asignacion
                    mejor_prioridad = prioridad

    return mejor_asignacion, mejor_puntaje

def leer_lista(robot):
    lista = robot.lista_colores

    if len(lista) < 12:
        print("ERROR: lista incompleta")
        print(lista)
        return None

    grupo1 = [lista[0], lista[1], lista[6], lista[7]]
    grupo2 = [lista[2], lista[3], lista[4], lista[5]]
    grupo3 = [lista[8], lista[9], lista[10], lista[11]]

    grupos = [grupo1, grupo2, grupo3]

    asignacion, puntaje = elegir_mejor_asignacion(grupos)

    print("Grupo 1:", grupo1, "→", asignacion[0])
    print("Grupo 2:", grupo2, "→", asignacion[1])
    print("Grupo 3:", grupo3, "→", asignacion[2])
    print("Puntaje estimado:", puntaje, "/ 120")

    return asignacion[0], asignacion[1], asignacion[2]

def construccion_pala2(robot):
    giroscopio(0, 10, 150, 1, robot)
    SA_posicion_relativa_cm(147, 0, 300, 1, robot)
    SA_posicion_relativa(0, -250, -400, 2, robot)
    giroscopio(90, -150, 150, 1, robot)
    SA_posicion_relativa(90, -50, -300, 2, robot)

def distancia_por_color(color):
    if color == Color.YELLOW:
        return 435
    elif color == Color.BLUE:
        return 615
    elif color == Color.GREEN:
        return 810
    elif color == Color.WHITE:
        return 1160
    else:
        print("Color no reconocido:", color)
        return None

def ir_por_bloques(color_detectado, robot):
    distancia_calculada = distancia_por_color(color_detectado)

    if distancia_calculada is None:
        return

    SA_posicion_relativa(90, distancia_calculada, 300, 1, robot)
    giroscopio(0, -150, 150, 2, robot)

def dejar_bloques(robot):
    robot.motor_ga.run_angle(300, -100)
    robot.motor_le.run_angle(300, -60)

def dejar_grupo1(robot):
    SA_posicion_relativa(0, 100, 250, 1, robot)
    giroscopio(-90, -150, 150, 2, robot)
    SA_posicion_relativa(-90, 50, 300, 1, robot)
    giroscopio(-175, -150, 150, 2, robot)
    SA_posicion_relativa(0, -700, -300, 2, robot)
    giroscopio(0, 150, 50, 2, robot)
    SA_posicion_relativa(0, 400, 300, 1, robot)

def escombros_azules(robot):
    SA_posicion_relativa_cm(23, 45, -300, 2, robot)
    giroscopio(21, -150, 150, 4, robot)
    SA_posicion_relativa_cm(51, 21, -300, 2, robot)
    giroscopio(175, -150, 150, 4, robot)
    SA_posicion_relativa(0, 75, 150, 1, robot)
    robot.motor_ga.run_angle(300, -235)
    SA_posicion_relativa(0, 50, 250, 1, robot)
    robot.motor_ga.run_angle(300, -75)
    wait(100)
    SA_posicion_relativa(0, -150, -300, 2, robot)

#configurar()
#limpiar_llantas(robot)
#test(robot)

def main(robot):
    construccion_pala1_bloque0cemento(robot)
    escombros_blancos(robot)
    leer_color(robot)
    color1, color2, color3 = leer_lista(robot)
    escombros_azules(robot)
    construccion_pala2(robot)
    ir_por_bloques(color1, robot)
    recoger_bloques(robot)
    dejar_grupo1(robot)

construccion_pala1_bloque0cemento(robot)