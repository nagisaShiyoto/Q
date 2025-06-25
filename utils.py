import socket
from dataclasses import dataclass

MSG_SIZE = 1024
EXIT_MSG = "/exit"
TRANSFER_MSG = "/transfer "
UNICAST_MSG = "/unicast "
UNICAST_PARAMS_AMOUNT = 3
NORMAL_STARTING_SLASH = "//"
ADMIN_ROOM_NAME = "*"
ADMIN_PASSWORD = "password"


@dataclass
class user:
    user_name: str
    room_name: str
    my_socket: socket.socket
