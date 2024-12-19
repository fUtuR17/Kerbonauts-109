import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Параметры ракеты (как в предыдущем коде)
M0 = 14125  # Начальная масса ракеты с топливом (кг)
MT = 10000  # Масса топлива (кг)
u = 2050    # Скорость истечения газов (м/с)
burn_rate = 68.5  # Расход топлива (кг/с)
Cd = 0.32  # Коэффициент аэродинамического сопротивления
A = 1.33   # Площадь поперечного сечения ракеты (м^2)
rho0 = 1.225  # Плотность воздуха на уровне моря (кг/м^3)
H = 7000   # Характеристическая высота атмосферы (м)
g = 9.81   # Ускорение свободного падения (м/с^2)
mu = 3.53e12  # Гравитационный параметр (м^3/с^2)
R_planet = 600e3  # Радиус планеты (м)

# Время
dt = 0.1  # Шаг времени (с)
time_total = np.arange(0, 130, dt)  # Время полета (секунды)

# Инициализация массивов для хранения значений
height = np.zeros_like(time_total)  # Высота
velocity = np.zeros_like(time_total)  # Скорость
mass = np.zeros_like(time_total)  # Масса ракеты

# Начальные условия
height[0] = 0
velocity[0] = 0
mass[0] = M0

# Расчет динамики ракеты
for i in range(1, len(time_total)):
    t = time_total[i]

    # Определяем, есть ли еще топливо
    if mass[i - 1] > M0 - MT:
        thrust = u * burn_rate  # Тяга
        mass[i] = mass[i - 1] - burn_rate * dt  # Обновляем массу
    else:
        thrust = 0  # Топливо закончилось, тяги нет
        mass[i] = mass[i - 1]  # Масса остается постоянной

    # Вычисляем плотность воздуха (экспоненциальное уменьшение с высотой)
    rho = rho0 * np.exp(-height[i - 1] / H)

    # Силы: тяга, сопротивление воздуха, гравитация
    drag = 0.5 * Cd * A * rho * velocity[i - 1]**2
    gravity = mu / (R_planet + height[i - 1])**2

    # Ускорение ракеты по второму закону Ньютона
    acceleration = ((thrust - drag - mass[i] * gravity) / mass[i])/2

    # Обновляем скорость и высоту
    velocity[i] = (velocity[i - 1] + acceleration * dt)
    height[i] = max(height[i - 1] + velocity[i] * dt, 0)

# Загрузка данных из CSV
csv_file_path = "data.csv"  # Укажите путь к файлу
csv_data = pd.read_csv(csv_file_path)


# Предполагаем, что в CSV есть столбцы "Time", "Velocity", "Height"
csv_time = csv_data["Time"]
csv_height = csv_data["Height"]
csv_velocity = csv_data["Velocity"]

# Построение графиков
plt.figure(figsize=(12, 6))

# График скорости
plt.subplot(1, 2, 1)
plt.plot(time_total, velocity, label="Расчетная скорость")
plt.plot(csv_time, csv_velocity, label="Скорость из CSV", linestyle="--")
plt.xlabel("Время (с)")
plt.ylabel("Скорость (м/с)")
plt.title("Скорость от времени")
plt.grid()
plt.legend()

# График высоты
plt.subplot(1, 2, 2)
plt.plot(time_total, height, label="Расчетная высота", color="orange")
plt.plot(csv_time, csv_height, label="Высота из CSV", linestyle="--", color="red")
plt.xlabel("Время (с)")
plt.ylabel("Высота (м)")
plt.title("Высота от времени")
plt.grid()
plt.legend()

plt.tight_layout()
plt.savefig('rocket_simulation_two_stages.png')
