import threading
import time
import uuid
import serial

from configuration import configuration


class MockSerial:
    def __init__(self, com, baud_Rate) -> None:
        pass

    def flushInput(self):
        pass

    def write(self, encoded_string):
        print(f"{int(time.monotonic() * 1000)}, {encoded_string.decode('utf-8').strip()}")

    def close(self):
        pass


# for debug purpose...
debug = configuration["COM"]["debug"]
if debug == True:
    serial.Serial = MockSerial


class TcodeInstruction:
    def __init__(
        self,
        axis,
        value,
        duration_ms,
    ) -> None:
        self._axis = axis
        self._value = value
        self._duration_ms = duration_ms

    def __str__(self) -> str:
        return f"{self._axis}{self._value:02d}I{self._duration_ms}"

    @property
    def duration_ms(self):
        return self._duration_ms


class TcodeLine:
    def __init__(self, instructions: list[TcodeInstruction]) -> None:
        self._instructions = instructions

    def __str__(self) -> str:
        return " ".join(str(i) for i in self._instructions) + "\n"

    def strip(self):
        return str(self).strip()

    def encode(self):
        return str(self).encode()

    @property
    def duration_ms(self):
        return max([s.duration_ms for s in self._instructions])


class TcodeFire(threading.Thread):
    def __init__(self, com, baud_rate, *args, **kwarg) -> None:
        super().__init__()
        self._queue = []
        self._mode = "running"
        self._serial_channel = None
        self._com = com
        self._baud_rate = baud_rate
        self._session_id = str(uuid.uuid4())

    def push_instruction(self, instruction: TcodeLine):
        self._queue.append(instruction)

    def push_instructions(self, *instruction):
        self._queue.extend(instruction)

    def clear(self):
        self._queue.clear()
        self._session_id = str(uuid.uuid4())

    def stop_thread(self):
        self._serial_channel.close()
        self._mode = "stop"

    def start_thread(self):
        self._mode = "running"
        self._serial_channel = serial.Serial(self._com, self._baud_rate)  # COM, 115200)
        self._serial_channel.flushInput()
        # self._serial_channel.write("L005I2000".encode())
        # time.sleep(2.5)
        self.start()

    def delay(self, time_ms):
        current_session_id = self._session_id
        end_time_ms = int(time.monotonic() * 1000) + time_ms
        while int(time.monotonic() * 1000) < end_time_ms and current_session_id == self._session_id:
            time.sleep(0.01)
            # pass

    def run(self) -> None:
        while self._mode == "running":

            if len(self._queue) != 0:
                instruction = self._queue.pop(0)
                s = int(time.monotonic() * 1000)
                # self._serial_channel.write()
                self._serial_channel.write(instruction.encode())
                e = int(time.monotonic() * 1000)
                delay_for = instruction.duration_ms - (e - s)
                try:
                    # time.sleep((delay_for * 0.99) / 1000)
                    self.delay(delay_for)
                except ValueError:
                    pass

    def __len__(self):
        return len(self._queue)
