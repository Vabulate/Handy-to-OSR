import math
import random
from itertools import count, cycle
from functools import partial

from configuration import configuration
from tcode_fire import TcodeInstruction, TcodeLine

INIT_TIME_DURATION_MS = 300


def calculate_bpm(distance_mm, velocity_mm_per_s):
    # Calculate the time for a complete cycle (down and up)
    print(distance_mm, velocity_mm_per_s)
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
    # back = surge_absolute_position(relative_back)
    # forth = surge_absolute_position(relative_forth)
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
            ]
        )
        yield TcodeLine(
            [
                TcodeInstruction("L0", bottom, duration_down),
                TcodeInstruction(L1_R1, forth, duration_down),
                TcodeInstruction("R0", 0, duration_down),
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
    # roll_radius = (abs(back - forth) + 1) * ROLL_RADIUS_FACTOR
    # angular_speed_roll = linear_speed / roll_radius
    angular_speed_roll = calculate_angular_velocity(abs(top - bottom), linear_speed)
    # twist
    t0 = twist_absolute_position(100)
    t1 = twist_absolute_position(0)
    twist_radius = abs(t0 - t1) + 1
    angular_speed_twist = linear_speed / twist_radius
    t = 0
    yield TcodeLine(
        [
            TcodeInstruction("L0", next(top_to_bottom), INIT_TIME_DURATION_MS),
            TcodeInstruction(
                "R1",
                get_orbital_position(angular_speed_roll * t, back, forth, 1, -0.1),
                INIT_TIME_DURATION_MS,
            ),
            TcodeInstruction(
                "R0",
                get_orbital_position(angular_speed_twist * t, t0, t1, -1, 0.1),
                INIT_TIME_DURATION_MS,
            ),
        ]
    )
    while True:
        t += step_size_ms
        yield TcodeLine(
            [
                TcodeInstruction("L0", next(top_to_bottom), step_size_ms),
                TcodeInstruction(
                    "R1",
                    get_orbital_position(angular_speed_roll * t, back, forth, 1, -0.1),
                    step_size_ms,
                ),
                TcodeInstruction(
                    "R0",
                    get_orbital_position(angular_speed_twist * t, t0, t1, -1, 0.1),
                    step_size_ms,
                ),
            ]
        )


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
    t = 0
    yield TcodeLine(
        [
            TcodeInstruction("L0", next(top_to_bottom), INIT_TIME_DURATION_MS),
            TcodeInstruction(
                "R2",
                get_orbital_position(angular_speed_pitch * t, back, forth, 1, -0.1),
                INIT_TIME_DURATION_MS,
            ),
            TcodeInstruction(
                "R0",
                get_orbital_position(angular_speed_twist * t, t0, t1, -1, 0.1),
                INIT_TIME_DURATION_MS,
            ),
        ]
    )
    while True:
        t += step_size_ms
        yield TcodeLine(
            [
                TcodeInstruction("L0", next(top_to_bottom), step_size_ms),
                TcodeInstruction(
                    "R2",
                    get_orbital_position(angular_speed_pitch * t, back, forth, 1, -0.1),
                    step_size_ms,
                ),
                TcodeInstruction(
                    "R0",
                    get_orbital_position(angular_speed_twist * t, t0, t1, -1, 0.1),
                    step_size_ms,
                ),
            ]
        )


def long_stroke(
    relative_top, relative_bottom, relative_back, relative_forth, linear_speed
):
    step_size_ms = 50

    # Stroke
    top = stroke_absolute_position(relative_top)
    bottom = stroke_absolute_position(relative_bottom)
    stroke_increment = max([int(step_size_ms * linear_speed), 1])
    top_to_bottom = list(range(top, bottom - stroke_increment, -1 * stroke_increment))
    top_to_bottom = cycle(top_to_bottom + list(reversed(top_to_bottom[0:-1])))

    # Surge
    back = surge_absolute_position(relative_back)
    forth = surge_absolute_position(relative_forth)
    surge_increment = max([int(step_size_ms * linear_speed), 1])
    back_to_forth = list(range(back, forth - surge_increment, -1 * surge_increment))
    back_to_forth = cycle(back_to_forth + list(reversed(back_to_forth[0:-1])))
    t = 0
    while True:
        t += step_size_ms
        yield TcodeLine(
            [
                TcodeInstruction("L0", next(top_to_bottom), step_size_ms),
                TcodeInstruction("L1", next(back_to_forth), step_size_ms),
            ]
        )


def tempest_stroke(bpm, from_, to, phase, ecc):
    frequency = 50
    angular_velocity = (2 * math.pi * bpm) / 60
    scale = 0.5 * abs(to - from_)
    midpoint = 0.5 * (to + from_)
    index = count()
    while True:
        angle = ((next(index) * angular_velocity) / frequency) + (0.5 * math.pi * phase)
        yield int(midpoint - scale * math.cos(angle + (ecc * math.sin(angle))))


def tempest_stroke_pitched_stroke(relative_top, relative_bottom, linear_speed):
    step_size_ms = 50
    top = stroke_absolute_position(relative_top)
    bottom = stroke_absolute_position(relative_bottom)
    back = pitch_absolute_position(100)
    forth = pitch_absolute_position(0)
    t0 = twist_absolute_position(100)
    t1 = twist_absolute_position(0)
    bpm = calculate_bpm(abs(top - bottom), linear_speed) * 4
    print("BPM = ", bpm)
    stroke_gen = tempest_stroke(bpm, bottom, top, 0, 0)
    pitch_gen = tempest_stroke(
        calculate_bpm(abs(back - forth), linear_speed), back, forth, 1, -0.1
    )
    twist_gen = tempest_stroke(bpm, t1, t0, 2, 0.1)
    yield TcodeLine(
        [
            TcodeInstruction("L0", next(stroke_gen), INIT_TIME_DURATION_MS),
            TcodeInstruction(
                "R2",
                next(pitch_gen),
                INIT_TIME_DURATION_MS,
            ),
            TcodeInstruction(
                "R0",
                next(twist_gen),
                INIT_TIME_DURATION_MS,
            ),
        ]
    )
    while True:
        yield TcodeLine(
            [
                TcodeInstruction("L0", next(stroke_gen), step_size_ms),
                TcodeInstruction(
                    "R2",
                    next(pitch_gen),
                    step_size_ms,
                ),
                TcodeInstruction(
                    "R0",
                    next(twist_gen),
                    step_size_ms,
                ),
            ]
        )


if __name__ == "__main__":
    gen = long_stroke(100, 0, 100, 0, 200 / 1000)
    for i in range(50):
        print(next(gen).strip())
