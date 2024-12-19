import math
import krpc
import time

# Подключаемся к KSP
conn = krpc.connect(name='Falcon 1 v3')
vessel = conn.space_center.active_vessel

body = conn.space_center.bodies['Kerbin']

# Создаём потоки из которых нужно брать данные
altitude_stream = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')

mass_stream = conn.add_stream(getattr, vessel, 'mass')

velocity_stream = conn.add_stream(vessel.velocity, body.reference_frame)

start_time = time.time()

# Файл, в который записываются логи
file = open(f'log_{int(start_time)}.csv', 'w')

while True:
    mass = mass_stream()
    altitude = altitude_stream()
    velocity_axises = velocity_stream()

    velocity = math.sqrt(velocity_axises[0] ** 2 + velocity_axises[1] ** 2 + velocity_axises[2] ** 2)

    current_time = time.time()

    line = f'{round(current_time - start_time, 2)};{round(mass, 2)};{round(altitude, 2)};{round(velocity, 2)}'

    print(f'{line}')  # ; vel={tuple(map(lambda a: round(a, 2), velocity_axises))}

    file.write(f'{line}\n')
    file.flush()

    time.sleep(1)
