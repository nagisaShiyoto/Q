import socket
MSG_SIZE = 1024
EXIT_MSG = "/exit"
TRANSFER_MSG = "/transfer "
ADMIN_ROOM_NAME = "*"
class user:
    # create the struct of user, with all the needed data
    def __init__(self, user_name: str, room_name: str, my_socket: socket.socket ):
        self._user_name = user_name
        self._room_name = room_name
        self._my_socket = my_socket
