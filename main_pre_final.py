import math
import time
import krpc
# Исправить/доделать
# 1) Отстыковка по уровню топлива, а не по высоте
# 2) Понимать, как устроена механика движения на орбите
# 3) Понимать, как доставать логи из krpc
turn_start_altitude = 2000
turn_end_altitude = 45000
target_altitude = 100000
max_turn_angle = 88

conn = krpc.connect(name='Falcon 1 v2')
vessel = conn.space_center.active_vessel

# Set up streams for telemetry
ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
# stage_5_resources = vessel.resources_in_decouple_stage(stage=5, cumulative=False)
# srb_5_fuel = conn.add_stream(stage_5_resources.amount, 'LiquidFuel')
# stage_4_resources = vessel.resources_in_decouple_stage(stage=4, cumulative=False)
# srb_4_fuel = conn.add_stream(stage_5_resources.amount, 'LiquidFuel')
# stage_3_resources = vessel.resources_in_decouple_stage(stage=3, cumulative=False)
# srb_3_fuel = conn.add_stream(stage_5_resources.amount, 'LiquidFuel')
# stage_2_resources = vessel.resources_in_decouple_stage(stage=2, cumulative=False)
# srb_2_fuel = conn.add_stream(stage_5_resources.amount, 'LiquidFuel')
# stage_1_resources = vessel.resources_in_decouple_stage(stage=1, cumulative=False)
# srb_1_fuel = conn.add_stream(stage_5_resources.amount, 'LiquidFuel')
# stage_0_resources = vessel.resources_in_decouple_stage(stage=0, cumulative=False)
# srb_0_fuel = conn.add_stream(stage_5_resources.amount, 'LiquidFuel')

# perigee = conn.add_stream(getattr, vessel.orbit, 'perigr')
# print(dir(first_stage_fuel))
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

# Main ascent loop
first_stage_separated = False
turn_angle = 0
while True:
    # print(f"5: {srb_5_fuel()}")
    # print(f"4: {srb_4_fuel()}")
    # print(f"3: {srb_3_fuel()}")
    # print(f"2: {srb_2_fuel()}")
    # print(f"1: {srb_1_fuel()}")
    # print(f"0: {srb_0_fuel()}")
    # current_stage_resources = vessel.resources_in_decouple_stage(stage=3, cumulative=False)
    # current_stage_fuel = conn.add_stream(stage_5_resources.amount, 'LiquidFuel')
    # if s:
    #     vessel.control.activate_next_stage()
    # Gravity turn
    if turn_start_altitude < altitude() < turn_end_altitude:
        frac = ((altitude() - turn_start_altitude) /
                (turn_end_altitude - turn_start_altitude))
        new_turn_angle = frac * 90
        if abs(new_turn_angle - turn_angle) > 0.5:
            turn_angle = new_turn_angle
            vessel.auto_pilot.target_pitch_and_heading(90 - turn_angle, 90)
        if altitude() >= 23000:
            if not first_stage_separated:
                vessel.control.activate_next_stage()
                first_stage_separated = True
                time.sleep(3)
                vessel.control.throttle = 0.6
                vessel.control.activate_next_stage()
            # vessel.control.activate_next_stage()
    # Separate SRBs when finished
    # if not srbs_separated:
    #     if srb_fuel() < 0.1:
    #         vessel.control.activate_next_stage()
    #         srbs_separated = True
    #         print('SRBs separated')

    # Decrease throttle when approaching target apoapsis
    if apoapsis() > target_altitude*0.9:
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
v1 = math.sqrt(mu*((2./r)-(1./a1)))
v2 = math.sqrt(mu*((2./r)-(1./a2)))
delta_v = v2 - v1
node = vessel.control.add_node(
    ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)
# Calculate burn time (using rocket equation)
F = vessel.available_thrust
Isp = vessel.specific_impulse * 9.82
m0 = vessel.mass
m1 = m0 / math.exp(delta_v/Isp)
flow_rate = F / Isp
burn_time = (m0 - m1) / flow_rate

# Orientate ship
print('Orientating ship for circularization burn')
vessel.auto_pilot.reference_frame = node.reference_frame
vessel.auto_pilot.target_direction = (0, 1, 0)
vessel.auto_pilot.wait()

# Wait until burn
print('Waiting until circularization burn')
burn_ut = ut() + vessel.orbit.time_to_apoapsis - (burn_time/2.)
lead_time = 5
conn.space_center.warp_to(burn_ut - lead_time)
# Execute burn
print('Ready to execute burn')
time_to_apoapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
while time_to_apoapsis() - (burn_time/2.) > 0:
    pass
print('Executing burn')
vessel.control.throttle = 1.0
time.sleep(burn_time - 0.1)
print('Fine tuning')
vessel.control.throttle = 0.05
remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
while remaining_burn()[1] > 0:
    pass
vessel.control.throttle = 0.0
node.remove()

print('Launch complete')
