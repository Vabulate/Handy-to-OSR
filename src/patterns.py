import math
import random
from itertools import count, cycle
from functools import partial

from configuration import configuration
from tcode_fire import TcodeInstruction, TcodeLine

INIT_TIME_DURATION_MS = 300


def calculate_bpm(distance_mm, velocity_mm_per_s):
    # Calculate the time for a complete cycle (down and up)
    # print(distance_mm, velocity_mm_per_s)
    time_per_cycle_s = (distance_mm * 2) / velocity_mm_per_s

    return 60 / time_per_cycle_s


def calculate_angular_velocity(distance, linear_speed):
    # Convert BPM to frequency (Hz)
    frequency_hz = calculate_bpm(distance, linear_speed) / 60

    # Calculate angular velocity (radians per second)
    angular_velocity = 2 * math.pi * frequency_hz

    return angular_velocity


def get_orbital_position(angle, top_limit, bottom_limit, phase, ecc):
    midpoint = (top_limit + bottom_limit) / 2
    range_val = (top_limit - bottom_limit) / 2

    return int(
        midpoint
        + range_val
        * math.cos(
            angle + phase * math.pi / 2 + ecc * math.sin(angle + phase * math.pi / 2)
        )
    )


def get_absolute_position(min_bound, max_bound, relative_position):

    if not (0 <= relative_position <= 100):
        raise ValueError("Relative position must be between 0 and 100")

    # Calculate the absolute position
    absolute_position = min_bound + (
        (max_bound - min_bound) * (relative_position / 100.0)
    )
    return int(absolute_position)


ranges = configuration["ranges"]
stroke_absolute_position = partial(
    get_absolute_position,
    ranges["stroke"]["min"],
    ranges["stroke"]["max"],
)  # L0
surge_absolute_position = partial(
    get_absolute_position,
    ranges["surge"]["min"],
    ranges["surge"]["max"],
)  # L1
sway_absolute_position = partial(
    get_absolute_position,
    ranges["sway"]["min"],
    ranges["sway"]["max"],
)  # L2
twist_absolute_position = partial(
    get_absolute_position,
    ranges["twist"]["min"],
    ranges["twist"]["max"],
)  # R0
roll_absolute_position = partial(
    get_absolute_position,
    ranges["roll"]["min"],
    ranges["roll"]["max"],
)  # R1
pitch_absolute_position = partial(
    get_absolute_position,
    ranges["pitch"]["min"],
    ranges["pitch"]["max"],
)  # R2
valve_absolute_position = partial(
    get_absolute_position,
    ranges["valve"]["min"],
    ranges["valve"]["max"],
)  # A0


def costumed_stroke_half_twist_costumed_surge_smooth_motion_generator(
    relative_top,
    relative_bottom,
    relative_back,
    relative_forth,
    total_duration,
):
    factor = int(total_duration // 2 * 0.1)
    duration_up = total_duration // 2 + random.randint(-1 * factor, factor + 1)
    duration_down = total_duration - duration_up
    top = stroke_absolute_position(relative_top)
    bottom = stroke_absolute_position(relative_bottom)
    valve_0 = valve_absolute_position(0)
    valve_1 = valve_absolute_position(100)
    while True:
        L1_R1 = random.choice(["L1", "R1"])
        if L1_R1 == "L1":
            back = surge_absolute_position(relative_back)
            forth = surge_absolute_position(relative_forth)
        else:  # R1
            back = roll_absolute_position(relative_back)
            forth = roll_absolute_position(relative_forth)
        yield TcodeLine(
            [
                TcodeInstruction("L0", top, duration_up),
                TcodeInstruction(L1_R1, back, duration_up),
                TcodeInstruction("R0", 50, duration_up),
                TcodeInstruction("A0", valve_1, duration_up),
            ]
        )
        yield TcodeLine(
            [
                TcodeInstruction("L0", bottom, duration_down),
                TcodeInstruction(L1_R1, forth, duration_down),
                TcodeInstruction("R0", 0, duration_down),
                TcodeInstruction("A0", valve_0, duration_up),
            ]
        )


def full_stroke_with_roll_motion(
    relative_top, relative_bottom, relative_back, relative_forth, linear_speed
):
    step_size_ms = 50

    # Stroke
    top = stroke_absolute_position(relative_top)
    bottom = stroke_absolute_position(relative_bottom)
    stroke_increment = max([int(step_size_ms * linear_speed), 1])
    top_to_bottom = list(range(top, bottom - stroke_increment, -1 * stroke_increment))
    top_to_bottom = cycle(top_to_bottom + list(reversed(top_to_bottom[0:-1])))

    # ROLL
    back = roll_absolute_position(relative_back)
    forth = roll_absolute_position(relative_forth)
    angular_speed_roll = calculate_angular_velocity(abs(top - bottom), linear_speed)
    # twist
    t0 = twist_absolute_position(100)
    t1 = twist_absolute_position(0)
    twist_radius = abs(t0 - t1) + 1
    angular_speed_twist = linear_speed / twist_radius

    # valve
    valve_0 = valve_absolute_position(100)
    valve_1 = valve_absolute_position(0)
    valve_radius = abs(valve_0 - valve_1) + 1
    angular_speed_valve = linear_speed / valve_radius
    t = 0
    delay_time = INIT_TIME_DURATION_MS
    while True:
        t += step_size_ms
        yield TcodeLine(
            [
                TcodeInstruction("L0", next(top_to_bottom), delay_time),
                TcodeInstruction(
                    "R1",
                    get_orbital_position(angular_speed_roll * t, back, forth, 1, -0.1),
                    delay_time,
                ),
                TcodeInstruction(
                    "R0",
                    get_orbital_position(angular_speed_twist * t, t0, t1, -1, 0.1),
                    delay_time,
                ),
                TcodeInstruction(
                    "A0",
                    get_orbital_position(
                        angular_speed_valve * t, valve_0, valve_1, -1, 0.1
                    ),
                    delay_time,
                ),
            ]
        )
        delay_time = step_size_ms


def full_stroke_with_pitch_motion(
    relative_top, relative_bottom, relative_back, relative_forth, linear_speed
):
    step_size_ms = 50

    # Stroke
    top = stroke_absolute_position(relative_top)
    bottom = stroke_absolute_position(relative_bottom)
    stroke_increment = max([int(step_size_ms * linear_speed), 1])
    top_to_bottom = list(range(top, bottom - stroke_increment, -1 * stroke_increment))
    top_to_bottom = cycle(top_to_bottom + list(reversed(top_to_bottom[0:-1])))

    # PITCH
    back = pitch_absolute_position(relative_back)
    forth = pitch_absolute_position(relative_forth)

    angular_speed_pitch = calculate_angular_velocity(abs(top - bottom), linear_speed)
    # twist
    t0 = twist_absolute_position(100)
    t1 = twist_absolute_position(0)
    twist_radius = abs(t0 - t1) + 1
    angular_speed_twist = linear_speed / twist_radius

    # valve
    valve_0 = valve_absolute_position(100)
    valve_1 = valve_absolute_position(0)
    valve_radius = abs(valve_0 - valve_1) + 1
    angular_speed_valve = linear_speed / valve_radius
    delay_time = INIT_TIME_DURATION_MS
    t = 0

    while True:
        t += step_size_ms
        yield TcodeLine(
            [
                TcodeInstruction("L0", next(top_to_bottom), delay_time),
                TcodeInstruction(
                    "R2",
                    get_orbital_position(angular_speed_pitch * t, back, forth, 1, -0.1),
                    delay_time,
                ),
                TcodeInstruction(
                    "R0",
                    get_orbital_position(angular_speed_twist * t, t0, t1, -1, 0.1),
                    delay_time,
                ),
                TcodeInstruction(
                    "A0",
                    get_orbital_position(
                        angular_speed_valve * t, valve_0, valve_1, -1, 0.1
                    ),
                    delay_time,
                ),
            ]
        )
        delay_time = step_size_ms


def generate_wild_stroke_pattern(top, bottom, step_size_ms, linear_speed):
    # Compute the total range and split it into two halves
    mid = (top + bottom) // 2

    # First half: Half the speed (double the stroke increment)
    stroke_increment_half = max([int(step_size_ms * linear_speed / 2), 1])
    first_half = list(range(top, mid, -1 * stroke_increment_half))

    # Second half: Double the speed (half the stroke increment)
    stroke_increment_double = max([int(step_size_ms * linear_speed * 2), 1])
    second_half = list(range(mid, bottom, -1 * stroke_increment_double))

    # Upward motion: First half + second half
    upward = first_half + second_half

    # Downward motion: Reverse of upward motion
    downward = list(reversed(upward))

    # Combine upward and downward to form a cycle
    motion_pattern = cycle(upward + downward)

    return motion_pattern


def wild_stroke_and_pitch(
    relative_top, relative_bottom, relative_back, relative_forth, linear_speed
):
    step_size_ms = 50

    # Stroke
    top = stroke_absolute_position(relative_top)
    bottom = stroke_absolute_position(relative_bottom)

    top_to_bottom = generate_wild_stroke_pattern(
        top, bottom, step_size_ms, linear_speed
    )

    # PITCH
    back = pitch_absolute_position(relative_back)
    forth = pitch_absolute_position(relative_forth)

    angular_speed_pitch = calculate_angular_velocity(abs(top - bottom), linear_speed)
    # twist
    t0 = twist_absolute_position(100)
    t1 = twist_absolute_position(0)
    twist_radius = abs(t0 - t1) + 1
    angular_speed_twist = linear_speed / twist_radius

    # valve

    open_to_close = cycle([0, 10, 0, 20, 0, 30, 0, 40, 20, 50, 30, 60, 0, 0, 0, 0, 0])
    t = 0
    delay_time = INIT_TIME_DURATION_MS

    while True:
        t += step_size_ms
        yield TcodeLine(
            [
                TcodeInstruction("L0", next(top_to_bottom), delay_time),
                TcodeInstruction(
                    "R2",
                    get_orbital_position(angular_speed_pitch * t, back, forth, 1, -0.8),
                    delay_time,
                ),
                TcodeInstruction(
                    "R0",
                    get_orbital_position(angular_speed_twist * t, t0, t1, -1, 0.1),
                    delay_time,
                ),
                TcodeInstruction("A0", next(open_to_close), delay_time),
            ]
        )
        delay_time = step_size_ms


def long_stroke_1(
    relative_top, relative_bottom, relative_back, relative_forth, linear_speed
):
    step_size_ms = 50

    # Stroke
    top = stroke_absolute_position(relative_top)
    bottom = stroke_absolute_position(relative_bottom)
    stroke_increment = max([int(step_size_ms * linear_speed), 1])
    top_to_bottom = list(range(top, bottom - stroke_increment, -1 * stroke_increment))
    stroke_size = len(top_to_bottom)
    top_to_bottom = cycle(top_to_bottom + list(reversed(top_to_bottom[0:-1])))

    # Surge
    back = surge_absolute_position(relative_back)
    forth = surge_absolute_position(relative_forth)
    surge_increment = int(
        stroke_increment * ((abs(back - forth) // stroke_increment + 1) / stroke_size)
    )
    surge_increment = max([surge_increment, 1])
    back_to_forth = list(range(forth, back - surge_increment, -1 * surge_increment))
    back_to_forth = cycle(back_to_forth + list(reversed(back_to_forth[0:-1])))
    # valve
    valve_0 = valve_absolute_position(0)
    valve_100 = valve_absolute_position(100)
    valve_increment = int(
        stroke_increment
        * ((abs(valve_0 - valve_100) // stroke_increment + 1) / stroke_size)
    )
    valve_increment = max([valve_increment, 1])
    close_to_open = list(
        range(valve_100, max([valve_0 - valve_increment, 0]), -1 * valve_increment)
    )
    close_to_open = cycle(close_to_open + list(reversed(close_to_open[0:-1])))

    # pitch
    pitch_back = pitch_absolute_position(100)
    pitch_forth = pitch_absolute_position(0)

    angular_speed_pitch = calculate_angular_velocity(abs(top - bottom), linear_speed)

    # roll
    roll_back = roll_absolute_position(60)
    roll_forth = roll_absolute_position(30)

    angular_speed_roll = calculate_angular_velocity(abs(top - bottom), linear_speed)
    t = 0
    duration = INIT_TIME_DURATION_MS
    while True:
        t += step_size_ms
        yield TcodeLine(
            [
                TcodeInstruction("L0", next(top_to_bottom), duration),
                TcodeInstruction("L1", next(back_to_forth), duration),
                TcodeInstruction(
                    "R1",
                    get_orbital_position(
                        angular_speed_roll * t, roll_back, roll_forth, 1.5, -0.1
                    ),
                    duration,
                ),
                TcodeInstruction(
                    "R2",
                    get_orbital_position(
                        angular_speed_pitch * t, pitch_back, pitch_forth, 1, -0.1
                    ),
                    duration,
                ),
                TcodeInstruction("A0", next(close_to_open), duration),
            ]
        )
        duration = step_size_ms


def long_stroke_2(
    relative_top, relative_bottom, relative_back, relative_forth, linear_speed
):
    step_size_ms = 50

    # Stroke
    top = stroke_absolute_position(relative_top)
    bottom = stroke_absolute_position(relative_bottom)
    stroke_increment = max([int(step_size_ms * linear_speed), 1])
    top_to_bottom = list(range(top, bottom - stroke_increment, -1 * stroke_increment))
    stroke_size = len(top_to_bottom)
    top_to_bottom = cycle(top_to_bottom + list(reversed(top_to_bottom[0:-1])))

    # Surge
    back = surge_absolute_position(relative_back)
    forth = surge_absolute_position(relative_forth)
    surge_increment = int(
        stroke_increment * ((abs(back - forth) // stroke_increment + 1) / stroke_size)
    )
    surge_increment = max([surge_increment, 1])
    # print(back, )
    back_to_forth = list(range(forth, back - surge_increment, -1 * surge_increment))
    back_to_forth = cycle(back_to_forth + list(reversed(back_to_forth[0:-1])))

    # valve
    valve_0 = valve_absolute_position(0)
    valve_100 = valve_absolute_position(100)
    valve_increment = int(
        stroke_increment
        * ((abs(valve_0 - valve_100) // stroke_increment + 1) / stroke_size)
    )
    valve_increment = max([valve_increment, 1])
    close_to_open = list(
        range(valve_100, max([valve_0 - valve_increment, 0]), -1 * valve_increment)
    )
    close_to_open = cycle(close_to_open + list(reversed(close_to_open[0:-1])))

    # pitch
    pitch_back = pitch_absolute_position(100)
    pitch_forth = pitch_absolute_position(0)

    angular_speed_pitch = calculate_angular_velocity(abs(top - bottom), linear_speed)

    # roll
    roll_back = roll_absolute_position(100)
    roll_forth = roll_absolute_position(0)

    angular_speed_roll = calculate_angular_velocity(abs(top - bottom), linear_speed)
    t = 0
    duration = INIT_TIME_DURATION_MS
    while True:
        t += step_size_ms
        yield TcodeLine(
            [
                TcodeInstruction("L0", next(top_to_bottom), duration),
                TcodeInstruction("L1", next(back_to_forth), duration),
                TcodeInstruction(
                    "R1",
                    get_orbital_position(
                        angular_speed_roll * t, roll_back, roll_forth, 1, -0.5
                    ),
                    duration,
                ),
                TcodeInstruction(
                    "R2",
                    get_orbital_position(
                        angular_speed_pitch * t, pitch_back, pitch_forth, -1, -0.8
                    ),
                    duration,
                ),
                TcodeInstruction("A0", next(close_to_open), duration),
            ]
        )
        duration = step_size_ms


if __name__ == "__main__":
    gen = long_stroke_2(100, 0, 0, 100, 200 / 1000)
    with open("t1.txt", "w", encoding="utf-8") as tfile:
        for _ in range(200):
            tfile.write(next(gen).strip() + "\n")
