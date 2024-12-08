import math
import time
import krpc

turn_start_altitude = 2000
turn_end_altitude = 45000
target_altitude = 100000
max_turn_angle = 90
min_turn_angle = 0

conn = krpc.connect(name='Falcon 1 v3')
vessel = conn.space_center.active_vessel

# Set up streams for telemetry
ut = conn.add_stream(getattr, conn.space_center, 'ut')  # ut - universal time in KSP
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
#

# Pre-launch setup
vessel.control.sas = False
vessel.control.rcs = False
vessel.control.throttle = 1.0

# Countdown...
print('3...')
time.sleep(1)
print('2...')
time.sleep(1)
print('1...')
time.sleep(1)
print('Launch!')

vessel.control.activate_next_stage()
time.sleep(1)
vessel.control.activate_next_stage()
vessel.auto_pilot.engage()
vessel.auto_pilot.target_pitch_and_heading(90, 90)

stage_3_resources = vessel.resources_in_decouple_stage(stage=3, cumulative=False)
lqd_fuel = conn.add_stream(stage_3_resources.amount, 'LiquidFuel')

# Main ascent loop
first_stage_separated = False
turn_angle = 0

total_lqd_fuel = vessel.resources.amount('LiquidFuel')

while True:
    # Gravity turn
    if altitude() > turn_start_altitude and altitude() < turn_end_altitude:
        turn_angle = ((altitude() - turn_start_altitude) * (max_turn_angle - min_turn_angle)) / (
                    turn_end_altitude - turn_start_altitude) + min_turn_angle
        vessel.auto_pilot.target_pitch_and_heading(90 - turn_angle, 90)
        if not first_stage_separated:
            # if altitude() >= 23000:
            #     vessel.control.activate_next_stage()
            #     first_stage_separated = True
            #     time.sleep(3)
            #     vessel.control.throttle = 0.6
            #     vessel.control.activate_next_stage()
            if lqd_fuel() < 0.1:
                vessel.control.activate_next_stage()
                first_stage_separated = True
                time.sleep(3)
                vessel.control.throttle = 0.6
                vessel.control.activate_next_stage()
    # Decrease throttle when approaching target apoapsis
    if apoapsis() > target_altitude * 0.9:
        print('Approaching target apoapsis')
        break

# Disable engines when target apoapsis is reached
vessel.control.throttle = 0.25
while apoapsis() < target_altitude:
    pass
print('Target apoapsis reached')
vessel.control.throttle = 0.0

# Wait until out of atmosphere
print('Coasting out of atmosphere')
while altitude() < 70500:
    pass

# Plan circularization burn (using vis-viva equation)
print('Planning circularization burn')
mu = vessel.orbit.body.gravitational_parameter
r = vessel.orbit.apoapsis
a1 = vessel.orbit.semi_major_axis
a2 = r
v1 = math.sqrt(mu * ((2. / r) - (1. / a1)))  # Текущая скорость на орбите
v2 = math.sqrt(mu * ((2. / r) - (1. / a2)))  # Целевая скорость на орбите
delta_v = v2 - v1
node = vessel.control.add_node(
    ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)

# Calculate burn time (using rocket equation)
F = vessel.available_thrust
Isp = vessel.specific_impulse * 9.82
m0 = vessel.mass
m1 = m0 / math.exp(delta_v / Isp)
flow_rate = F / Isp
burn_time = (m0 - m1) / flow_rate  # Это общее время, необходимое горелке для достижения желаемого изменения скорости.

# Orientate ship
print('Orientating ship for circularization burn')
vessel.auto_pilot.reference_frame = node.reference_frame
vessel.auto_pilot.target_direction = (0, 1, 0)
vessel.auto_pilot.wait()

# Wait until burn
print('Waiting until circularization burn')
burn_ut = ut() + vessel.orbit.time_to_apoapsis - (burn_time / 2.)
lead_time = 5
conn.space_center.warp_to(burn_ut - lead_time)

# Execute burn
print('Ready to execute burn')
time_to_apoapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
while time_to_apoapsis() - (burn_time / 2.) > 0:
    pass
print('Executing burn')
vessel.control.throttle = 1.0
time.sleep(burn_time - 0.1)
vessel.control.throttle = 0
print('Launch complete')
