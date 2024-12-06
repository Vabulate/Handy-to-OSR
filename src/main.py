import json
import random
import time

from mitmproxy import http
from urllib.parse import urlparse, parse_qs

import patterns as patterns_module
from configuration import configuration
from tcode_fire import TcodeFire


HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Max-Age": "600",
}

state = {
    "stroke": {
        "bottom": 0,
        "top": 100,
    },
    "speed": 0,
    "mode": "halting",
    "direction": "up",
}


print("welcum to stroker proxy :)")
com = configuration["COM"]
t1 = TcodeFire(com["port"], com["baudrate"])
t1.start_thread()

SELECTIVE_PATTERNS = []
for name, flag in configuration["patterns"].items():
    if flag:
        print("selected - ", name)
        SELECTIVE_PATTERNS.append(getattr(patterns_module, name))
factors = configuration["factors"]


def send_success_response(flow: http.HTTPFlow) -> None:
    response = {
        "success": True,
        "connected": True,
        "result": 0,
        "state": 2,
        "fwVersion": "3.2.3-a28b8bb",
        "fwStatus": 0,
        "hwVersion": 1,
    }
    if state["mode"] == "halting":
        response["state"] = 1
    elif state["mode"] == "running":
        response["state"] = 2
    response["serverTime"] = int(time.time() * 1000)
    response["servertime"] = int(time.time() * 1000)
    flow.response = http.Response.make(200, json.dumps(response).encode(), HEADERS)


def set_state(key: str, value) -> None:
    """Sets the state for stroke, speed, or mode."""
    if key == "stroke":
        pass
    elif key == "mode" and value == 0:
        state["speed"] = 0

    else:
        state[key] = value
    t1.clear()
    print_state()
    if (
        state["mode"] == "running"
        and state["speed"] != 0
        and state["stroke"]["top"] != state["stroke"]["bottom"]
    ):
        total_time_ms = 0
        bottom = int(state["stroke"]["bottom"])
        top = int(state["stroke"]["top"])
        back = random.randint(0, 50)
        forth = random.randint(50, 100)
        if state["speed"] == 0:
            return

        patterns = []
        for selective_pattern in SELECTIVE_PATTERNS:
            patterns.append(selective_pattern(top, bottom, back, forth, state["speed"] / 1000))
        patterns.append(patterns_module.costumed_stroke_half_twist_costumed_surge_smooth_motion_generator(
                top, bottom, back, forth, state["speed"] / 1000
            ))

        # TODO: buffer strokes
        pattern = random.choice(patterns)
        print(f"current pattern = {pattern.__name__}")
        while total_time_ms < 1000 * 60 * 1.2:
            p = next(pattern)
            t1.push_instruction(p)

            total_time_ms += p.duration_ms


def get_query_param(query: dict, key: str, default: str) -> str:
    return query.get(key, [default])[0]


def handle_set_stroke(query: dict) -> None:
    type_ = get_query_param(query, "type", "mm")
    stroke_top = int(query["stroke"][0])

    if type_ != "%":  # should be in percentage
        stroke_top /= 2
    state["stroke"]["bottom"] = 0
    state["stroke"]["top"] = stroke_top
    set_state("stroke", stroke_top)


def handle_slide(body: dict) -> None:
    print(body)
    state["stroke"]["bottom"] = body.get("min", 0)
    state["stroke"]["top"] = body.get("max", 100)
    # max_ = body['max']
    set_state("stroke", state["stroke"]["top"])


def handle_set_speed(query: dict) -> None:
    type_ = get_query_param(query, "type", "mm/s")
    speed = int(query["speed"][0])
    if type_ == "%":
        speed = int(speed * factors["speed_factor"])

    set_state("speed", speed)


def handle_set_velocity(query: dict) -> None:
    speed = int(query["velocity"] * factors["velocity_factor"])
    set_state("speed", speed)


def handle_set_mode(query: dict) -> None:

    mode_value = get_query_param(query, "mode", "0")
    if mode_value == "0":
        set_state("mode", "halting")
        print("stopping device")
    elif mode_value == "1":

        set_state("mode", "running")
        print("running device")
    else:
        print("Unknown mode:", mode_value)


def print_state() -> None:
    stroke_range = state["stroke"]
    print(
        f"Current State -> Stroke: {stroke_range['bottom']} - {stroke_range['top']}, Speed: {state['speed']}, Mode: {state['mode']}"
    )


def request(flow: http.HTTPFlow) -> None:
    if "handyfeeling" not in flow.request.url:
        return

    parsed_url = urlparse(flow.request.url)

    action = parsed_url.path.split("/")[-1]
    # print(parsed_url.path)
    query = parse_qs(parsed_url.query)
    body = {}
    try:
        body = json.loads(flow.request.data.content.decode("utf-8"))
    except json.decoder.JSONDecodeError:
        pass
    if action == "setStroke":
        handle_set_stroke(query)
    elif action == "slide":
        if flow.request.method != "GET":
            handle_slide(body)
    elif action in ("setSpeed",):
        handle_set_speed(query)
    elif action in ("velocity",):
        if flow.request.method != "GET":
            handle_set_velocity(body)
    elif action in ("setMode", "mode"):
        print("setting mode...")
        handle_set_mode(query)
    elif action == "start":
        handle_set_mode({"mode": "1"})
    elif action == "stop":
        handle_set_mode({"mode": "0"})

    elif action in ("getStatus", "getVersion", "getServerTime"):
        pass
    elif action == "servertime":
        pass

    elif action == "latest":
        pass
    elif action == "info":
        pass

    elif action == "connected":
        pass
    elif action == "state":
        pass
    elif action == "setup":
        # wget script
        # script to tcode
        print(body)
    # elif action == "sse":
    #     print(body)
    else:

        print("error!", action)

    send_success_response(flow)
