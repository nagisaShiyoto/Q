import socket
import argparse
import utils
from typing import Tuple
import sys

WINDOWS = "win32"
LINUX = "linux"

if sys.platform == WINDOWS:
    import msvcrt
    ENTER_KEY = "\r"
elif sys.platform == LINUX:
    import select
    ENTER_KEY = "\n"


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

def connect_server(server_ip, server_port, name, room_name) -> utils.user:
    """
    connect to the server and identify(room and username)

    :param server ip: the server to connect for chatting
    :param server_port: the port the server use
    :param name: the wanted username
    :param room_name: the room he wanted to connect
    :param return: user with all the needed data
    """
    my_socket = socket.socket()
    my_socket.connect((server_ip, server_port))
    my_socket.send(f"{name} {room_name}".encode())
    my_socket.setblocking(False)
    return utils.user(name,room_name,my_socket)

def get_input(input: str) -> str:
    """
    get user's key using non-blocking technic and print it

    :param return: the key
    """
    if sys.platform == WINDOWS and msvcrt.kbhit():
        try:
            key = msvcrt.getch().decode()
            if key == ENTER_KEY:
                print()
            else:
                print(key, end="")
            return input + key
        except UnicodeDecodeError:
            print("\ncan't process last key")
            # clearing the buffer
            msvcrt.getch()
    elif sys.platform == LINUX:
        new_input,_,_ = select.select([sys.stdin],[],[],0)
        if new_input != []:
            return new_input[0].readline()
    
    return input

def transfer_room(input: str, client: utils.user) -> None:
    """
    transferring user room

    :param input: the msg with transfer info
    :param client: the user information
    """

    client.my_socket.send(input.encode())

    # waiting for response
    client.my_socket.setblocking(True)
    response = client.my_socket.recv(utils.MSG_SIZE).decode()
    client.my_socket.setblocking(False)
    
    if response.startswith(utils.TRANSFER_MSG):
        client.room_name = response.split(" ")[1]
        print(f"transferred to room {client.room_name}")
    else:
        print("could not transfer rooms:")
        print(response)

def send_message(input: str, client: utils.user) -> None:
    """
    sending message to server

    :param input: message to send
    :param client: all the needed user info
    """
    client.my_socket.send(input.encode())

def handle_sending(input: str, client: utils.user) -> None:
    """
    redirect all communication options

    :param input: the msg to send
    :param client: the user information
    """
    massage_redirector = {
        utils.COMMAND_START + utils.TRANSFER_MSG: transfer_room
    }

    first_argument = input.split(" ")[0]
    massage_redirector.get(first_argument, send_message)(input, client)

def handle_communication(client: utils.user) -> None:
    """
    handle all input\output communications between the server

    :param client: the needed client info for communication
    """
    input = ""
    logged_out = False
    while not logged_out:
        try:
            print(client.my_socket.recv(utils.MSG_SIZE).decode())
        # not got a massage -> check if want to send
        except BlockingIOError:
            pass
        input = get_input(input)
        if ENTER_KEY in input:
            input = input[:-1]
            handle_sending(input, client)
            if input == (utils.COMMAND_START + utils.EXIT_MSG):
                logged_out = True
            
            input = "" 

def main() -> None:
    server_ip, server_port, name, room_name = get_argues()
    try:
        client = connect_server(server_ip, server_port, name, room_name)
        handle_communication(client)
    except ConnectionRefusedError:
        print("server not found")
    except ConnectionResetError:
        print("server lost connection")
        client.my_socket.close()

if __name__ == "__main__":
    main()