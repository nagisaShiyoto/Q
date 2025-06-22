import socket
import argparse
import utils
import msvcrt
from typing import Tuple

ENTER_KEY = "\r"

def get_argues() -> Tuple[str, int, str, str]:
    """
    get all the needed argument from the command line

    :param return: server ip - the server to connect for chatting
    server_port - the port the server use
    name - the wanted username
    room_name - the room he wanted to connect
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('server_ip', type=str, help="the server to connect for chatting")
    parser.add_argument('server_port', type=int, help="the port the server use")
    parser.add_argument('name', type=str, help="your username")
    parser.add_argument('room_name', type=str, help="the room's name to connect to")
    args = parser.parse_args()
    return args.server_ip, args.server_port, args.name, args.room_name

def connect_server(server_ip, server_port, name, room_name):
    my_socket = socket.socket()
    my_socket.connect((server_ip, server_port))
    my_socket.send(f"{name} {room_name}".encode())
    my_socket.setblocking(False)
    return utils.user(name,room_name,my_socket)

def get_input(input: str):
    if msvcrt.kbhit():
        key = msvcrt.getch().decode()
        if key == ENTER_KEY:
            print()
        else:
            print(key, end="")
        return key
    return ""

def handle_communication(client: utils.user):
    input = ""
    logged_out = False
    while not logged_out:
        try:
            print(client._my_socket.recv(utils.MSG_SIZE).decode())
        
        # not got a massage -> check if want to send
        except BlockingIOError:
            input += get_input(input)
            if ENTER_KEY in input:
                input = input[:-1]
                client._my_socket.send(input.encode())
                if input == utils.EXIT_MSG:
                    logged_out = True
                
                input = "" 


def main():
    server_ip, server_port, name, room_name = get_argues()
    try:
        client = connect_server(server_ip, server_port, name, room_name)
        handle_communication(client)
    except ConnectionRefusedError:
        print("server not found")
    except ConnectionResetError:
        print("server lost connection")
        client._my_socket.close()
        

if __name__ == "__main__":
    main()