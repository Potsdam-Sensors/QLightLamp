import socket
from typing import Literal, Optional

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

    ARG_LAMP_OFF = "off"
    ARG_LAMP_ON = "on"
    ARG_LAMP_BLINK = "blink"

    LAMP_ARG_CMD_MAP = {
        ARG_LAMP_OFF: CMD_LAMP_OFF,
        ARG_LAMP_ON: CMD_LAMP_ON,
        ARG_LAMP_BLINK: CMD_LAMP_BLINK,
    }

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
            QLightST56EL.LAMP_ARG_CMD_MAP.get(red_lamp_state) or 0x00, # R
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
        return resp

    def set_lamp(self, red_lamp_state: Optional[Literal["off", "on", "blink"]]):
        return self._communicate(self._format_message(True, red_lamp_state))

    def lamp_off(self):
        return self.set_lamp(QLightST56EL.ARG_LAMP_OFF)

    def lamp_on(self):
        return self.set_lamp(QLightST56EL.ARG_LAMP_ON)
    
    def lamp_blink(self):
        return self.set_lamp(QLightST56EL.ARG_LAMP_BLINK)