import socket
import argparse
import select
from typing import List
from collections import defaultdict
import utils

socket_user_dict = {}
room_users_dict = defaultdict(list)

def get_port() -> int:
    """
    getting wanted server port from the commandline
    :param return: the wanted port
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('server_port', type=int, help="the port to use as the server")
    return parser.parse_args().server_port

def accept_user(listening_socket: socket.socket) -> None:
    """
    adding new found connection and making him identify(what room and name he has)

    :param listening_socket: the socket who is open to new conversations
    """
    client_socket, address = listening_socket.accept()
    msg = client_socket.recv(utils.MSG_SIZE).decode()
    user_name, room_name = msg.split(" ")

    curr_user = utils.user(user_name, room_name, client_socket)

    room_users_dict[curr_user._room_name].append(curr_user)
    socket_user_dict[client_socket] = curr_user

def initialize_server(port: int) -> socket.socket:
    """
    making all the first steps to make the server online

    :param port: the server's listening port
    :param return: a listening socket
    """
    SERVER_IP = ""  # listening to all inputs
    listening_socket = socket.socket()
    address =  (SERVER_IP, port)
    listening_socket.bind(address)
    listening_socket.listen()
    return listening_socket

def remove_user_from_room(user : utils.user) -> None:
    """
    removing specific user from the room

    :param user: the user to remove
    """
    room_users_dict[user._room_name].remove(user)
    if len(room_users_dict[user._room_name]) == 0:
        del room_users_dict[user._room_name]

def close_connection(user : utils.user) -> None:
    """
    closing the connection to a certain user

    :param user: the user to close connection with
    """
    del socket_user_dict[user._my_socket]
    remove_user_from_room(user)
    user._my_socket.close()

def send_all_messages(received_massage: str, user: utils.user) -> None:
    """
    sending the user's messages to all the users in his room(and admin)
    if he is a admin sends to everyone

    :param received_massage: the message the user sent
    :param user: the user who sent the messages
    """
    send_massage = f"{user._user_name} message: {received_massage}"
    if user._room_name != utils.ADMIN_ROOM_NAME:
        for to_send in room_users_dict[user._room_name]:
            to_send._my_socket.send(send_massage.encode())
        
        send_massage = f"message from room {user._room_name}, " + send_massage
        for to_send in room_users_dict[utils.ADMIN_ROOM_NAME]:
            to_send._my_socket.send(send_massage.encode())

    else:
        send_massage = "admin's massage, " + send_massage
        for user_list in room_users_dict.values():
            for to_send_user in user_list:
                to_send_user._my_socket.send(send_massage.encode())

def transfer_room(room_name: str, user: utils.user) -> None:
    """
    transferring users to another room

    :param room_name: the wanted room to switch to
    :param user: the user you switch room with
    """
    remove_user_from_room(user)
    user._room_name = room_name
    room_users_dict[room_name].append(user)

def handle_read(user: utils.user) -> None:
    """
    handling user message

    :param user: the user who sent the message
    """
    try:
        received_message = user._my_socket.recv(utils.MSG_SIZE).decode()
        if received_message == "" or received_message == utils.EXIT_MSG:
            close_connection(user)
            return
        elif received_message.startswith(utils.TRANSFER_MSG):
            transfer_room(received_message.split(" ")[1], user)
    except ConnectionResetError:
        close_connection(user)
        return
    
    
    send_all_messages(received_message, user)

def handle_socket_interaction(readable_sockets:List[socket.socket]) -> None:
    """
    handling any readable socket interaction

    :param readable_sockets: a list of readable socket(with new data) 
    """
    for read_socket in readable_sockets:
        users_socket = socket_user_dict[read_socket]
        if(users_socket == None):
            users_socket = accept_user(read_socket)
        else:
            handle_read(socket_user_dict[read_socket])

def main() -> None:
    server_port = get_port()
    listening_socket = initialize_server(server_port)

    socket_user_dict[listening_socket] = None

    while(True):
        readable_sockets, _, _ = select.select(socket_user_dict.keys(),[],[])
        handle_socket_interaction(readable_sockets)

if __name__ == "__main__":
    main()