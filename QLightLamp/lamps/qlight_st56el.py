import socket
from typing import Literal, Optional, Tuple

class QLightST56EL(object):
    """
    QLight's ST56EL-ETN

    Command the lamp's red light. May add sound later.

    Can likely easily be expanded for use with other ETN lights in sibling series.
    """
    CMD_READ = 0x52
    CMD_WRITE = 0x57
    CMD_LAMP_OFF = 0x00
    CMD_LAMP_ON = 0x01
    CMD_LAMP_BLINK = 0x02
    CMD_SOUND_OFF = 0x00
    CMD_SOUND_GROUPS = [0x00, 0x01, 0x02, 0x03, 0x04]
    CMD_SOUNDS = [0x01, 0x02, 0x03, 0x04, 0x05]

    RESP_ACK = 0x41 # A for 'Ack'

    ARG_LAMP_OFF = "off"
    ARG_LAMP_ON = "on"
    ARG_LAMP_BLINK = "blink"

    LAMP_ARG_CMD_MAP = {
        ARG_LAMP_OFF: CMD_LAMP_OFF,
        ARG_LAMP_ON: CMD_LAMP_ON,
        ARG_LAMP_BLINK: CMD_LAMP_BLINK,
    }

    LAMP_CMD_ARG_MAP = {
        CMD_LAMP_OFF: ARG_LAMP_OFF,
        CMD_LAMP_ON: ARG_LAMP_ON,
        CMD_LAMP_BLINK: ARG_LAMP_BLINK,
    }

    class Response(object):
        def __init__(self, b: bytes):
            assert not b or len(b) == 10, "expected either no bytes or 10 bytes"
            self.buf = b
            self.is_ack = b[0] == QLightST56EL.RESP_ACK
            self.sound_group = b[1]
            self.lamp_state_red, self.lamp_state_amber, self.lamp_state_green, self.lamp_state_blue, self.lamp_state_white = b[2:7]
            self.sound_channel = b[7]
            self.spare_0, self.spare_1 = b[8:10]
        
        def validate(self, quiet: bool = False) -> bool:
            if not self.is_ack:
                if not quiet: print(f"Message is not an 'ack', first byte was: 0x{self.buf[0]:X02}.")
                return False
            
            if self.sound_group not in QLightST56EL.CMD_SOUND_GROUPS:
                if not quiet: print(f"Sound group not one of {QLightST56EL.CMD_SOUND_GROUPS:02X}, got 0x{self.sound_group:02X}.")
            for lamp_state in [self.lamp_state_red, self.lamp_state_amber, self.lamp_state_green, self.lamp_state_blue, self.lamp_state_white]:
                if lamp_state not in [QLightST56EL.CMD_LAMP_BLINK, QLightST56EL.CMD_LAMP_OFF, QLightST56EL.CMD_LAMP_ON]:
                    if not quiet: print(f"Not all lamp states are valid, got 0x{lamp_state:02X}.")
                    return False
                
            if self.sound_channel and self.sound_channel not in QLightST56EL.CMD_SOUNDS:
                if not quiet: print(f"Sound channel is not one of {QLightST56EL.CMD_SOUNDS:02X}, got 0x{self.sound_channel:02X}.")
                return False
            
            if self.spare_0 or self.spare_1:
                if not quiet: print(f"Expected spare bytes to be empty, got 0x{self.spare_0:02X}, 0x{self.spare_1:02X}.")
                return False
            
            return True
        
        @staticmethod
        def _str_lamp(lamp_state: int) -> str:
            return f"{QLightST56EL.LAMP_CMD_ARG_MAP.get(lamp_state, f'ERR (0x{lamp_state:02X})')}"
        
        def __str__(self) -> str:
            is_valid = self.validate(True)
            return f"<Response{' [Invalid]' if not is_valid else ''}| R: {self._str_lamp(self.lamp_state_red)}, " + \
                    f"A: {self._str_lamp(self.lamp_state_amber)}, " + f"G: {self._str_lamp(self.lamp_state_green)}, " + \
                    f"B: {self._str_lamp(self.lamp_state_blue)}, " + f"W: {self._str_lamp(self.lamp_state_white)} | " + \
                    f"Sound (Grp. 0x{self.sound_group:02X}): {'off' if not self.sound_channel else f'0x{self.sound_channel}'}>"

        def __repr__(self) -> str:
            return self.__str__()
            

    def __init__(self, ip: str, port: int, timeout: float = 2.0):
        self.ip = ip
        self.port = port
        self.timeout = timeout
    
    def _format_message(self, write: bool, red_lamp_state: Optional[Literal["off", "on", "blink"]]):
        assert write or not red_lamp_state, "Cannot provide a lamp state for a read command."
        assert not write or red_lamp_state in [QLightST56EL.ARG_LAMP_BLINK, QLightST56EL.ARG_LAMP_OFF, QLightST56EL.ARG_LAMP_ON], "Lamp state must be one of \"off\", \"on\", \"blink\"."
        return bytes([
            QLightST56EL.CMD_WRITE if write else QLightST56EL.CMD_READ, # W / R
            0x00, # type / group
            QLightST56EL.LAMP_ARG_CMD_MAP.get(red_lamp_state) if write else 0x00, # R
            0x00, # Y
            0x00, # G
            0x00, # B
            0x00, # W
            0x00, # sound
            0x00,
            0x00
        ])

    def _communicate(self, cmd: bytes) -> bytes:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.ip, self.port))
        sock.sendall(cmd)
        resp = sock.recv(10)
        sock.close()
        if not resp:
            print("No response from lamp.")
        return resp

    def _verify_lamp_state(self, resp: Response, expected_lamp_state: Optional[Literal["off", "on", "blink"]]):
        expected_state = QLightST56EL.LAMP_ARG_CMD_MAP[expected_lamp_state]
        return resp.lamp_state_red == expected_state
    
    def set_lamp(self, red_lamp_state: Optional[Literal["off", "on", "blink"]]) -> Tuple[bool, Response]:
        resp = QLightST56EL.Response(self._communicate(self._format_message(True, red_lamp_state)))
        return self._verify_lamp_state(resp, red_lamp_state), resp

    def lamp_off(self):
        return self.set_lamp(QLightST56EL.ARG_LAMP_OFF)

    def lamp_on(self):
        return self.set_lamp(QLightST56EL.ARG_LAMP_ON)
    
    def lamp_blink(self):
        return self.set_lamp(QLightST56EL.ARG_LAMP_BLINK)
    
    def read_lamp(self):
        resp = self._communicate(self._format_message(False, None))
        return QLightST56EL.Response(resp)