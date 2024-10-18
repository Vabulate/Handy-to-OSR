import random
from functools import partial
from configuration import configuration
from tcode_fire import TcodeInstruction, TcodeLine


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


def costumed_stroke_half_twist_costumed_surge_smooth_motion(
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
    back = surge_absolute_position(relative_back)
    forth = surge_absolute_position(relative_forth)
    return TcodeLine(
        [
            TcodeInstruction("L0", top, duration_up),
            TcodeInstruction("L1", back, duration_up),
            TcodeInstruction("R0", 50, duration_up),
        ]
    ), TcodeLine(
        [
            TcodeInstruction("L0", bottom, duration_down),
            TcodeInstruction("L1", forth, duration_down),
            TcodeInstruction("R0", 0, duration_down),
        ]
    )


def costumed_stroke_half_twist_costumed_roll_smooth_motion(
    relative_top, relative_bottom, relative_back, relative_forth, total_duration
):
    factor = int(total_duration // 2 * 0.1)
    duration_up = total_duration // 2 + random.randint(-1 * factor, factor + 1)
    duration_down = total_duration - duration_up
    top = stroke_absolute_position(relative_top)
    bottom = stroke_absolute_position(relative_bottom)
    back = roll_absolute_position(relative_back)
    forth = roll_absolute_position(relative_forth)
    return TcodeLine(
        [
            TcodeInstruction("L0", top, duration_up),
            TcodeInstruction("R1", back, duration_up),
            TcodeInstruction("R0", 50, duration_up),
        ]
    ), TcodeLine(
        [
            TcodeInstruction("L0", bottom, duration_down),
            TcodeInstruction("R1", forth, duration_down),
            TcodeInstruction("R0", 0, duration_down),
        ]
    )


def costumed_stroke_half_twist_costumed_roll_fast_down_slow_up(
    relative_top, relative_bottom, relative_back, relative_forth, total_duration
):
    factor = int(total_duration // 2 * 0.1)
    nominator = random.choice([2, 3, 4, 5])
    denominator = nominator + 1
    duration_up = (total_duration * nominator) // denominator + random.randint(
        -1 * factor, factor + 1
    )
    duration_down = total_duration - duration_up
    top = stroke_absolute_position(relative_top)
    bottom = stroke_absolute_position(relative_bottom)
    back = roll_absolute_position(relative_back)
    forth = roll_absolute_position(relative_forth)
    return TcodeLine(
        [
            TcodeInstruction("L0", top, duration_up),
            TcodeInstruction("R1", back, duration_up),
            TcodeInstruction("R0", 50, duration_up),
        ]
    ), TcodeLine(
        [
            TcodeInstruction("L0", bottom, duration_down),
            TcodeInstruction("R1", forth, duration_down),
            TcodeInstruction("R0", 0, duration_down),
        ]
    )


def midway_full_twist_with_roll(
    relative_top, relative_bottom, relative_back, relative_forth, total_duration
):
    duration_twist_at_middle = 100
    total_duration = total_duration - duration_twist_at_middle*2

    duration_to_middle = total_duration//3
    duration_bottom = total_duration//3
    duration_top = total_duration//3

    top = stroke_absolute_position(relative_top)
    relative_middle = (relative_top + relative_bottom) // 2
    middle = stroke_absolute_position(relative_middle)
    bottom = stroke_absolute_position(relative_bottom)
    back = roll_absolute_position(relative_back)
    forth = roll_absolute_position(relative_forth)
    twist_start = twist_absolute_position(0)
    twist_end = twist_absolute_position(100)
    return (
        TcodeLine(
            [
                TcodeInstruction("L0", middle, duration_to_middle),
                TcodeInstruction("R1", back, duration_to_middle),
                TcodeInstruction("R0", 0, duration_to_middle),
            ]
        ),
        TcodeLine(
            [
                TcodeInstruction("L0", middle, duration_twist_at_middle),
                TcodeInstruction("R1", back, duration_twist_at_middle),
                TcodeInstruction("R0", twist_start, duration_twist_at_middle),
            ]
        ),
        TcodeLine(
            [
                TcodeInstruction("L0", middle, duration_twist_at_middle),
                TcodeInstruction("R1", forth, duration_twist_at_middle),
                TcodeInstruction("R0", twist_end, duration_twist_at_middle),
            ]
        ),
        TcodeLine(
            [
                TcodeInstruction("L0", top, duration_top),
                TcodeInstruction("R1", back, duration_top),
                TcodeInstruction("R0", 50, duration_top),
            ]
        ),
        TcodeLine(
            [
                TcodeInstruction("L0", bottom, duration_bottom),
                TcodeInstruction("R1", forth, duration_bottom),
                TcodeInstruction("R0", 0, duration_bottom),
            ]
        ),
    )
