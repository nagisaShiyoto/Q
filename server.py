import socket
import argparse
import select
from typing import List
from collections import defaultdict
import utils

SERVER_IP = ""  # listening to all inputs
TIME_OUT = 60

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

    room_users_dict[curr_user.room_name].append(curr_user)
    socket_user_dict[client_socket] = curr_user

def initialize_server(port: int) -> socket.socket:
    """
    making all the first steps to make the server online

    :param port: the server's listening port
    :param return: a listening socket
    """
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
    room_users_dict[user.room_name].remove(user)
    if len(room_users_dict[user.room_name]) == 0:
        del room_users_dict[user.room_name]

def close_connection(user : utils.user) -> None:
    """
    closing the connection to a certain user

    :param user: the user to close connection with
    """
    del socket_user_dict[user.my_socket]
    remove_user_from_room(user)
    user.my_socket.close()

def send_all_messages(received_massage: str, user: utils.user) -> None:
    """
    sending the user's messages to all the users in his room(and admin)
    if he is a admin sends to everyone

    :param received_massage: the message the user sent
    :param user: the user who sent the messages
    """
    send_massage = f"{user.user_name} message: {received_massage}"
    if user.room_name != (utils.ADMIN_ROOM_NAME + utils.ADMIN_PASSWORD):
        for to_send in room_users_dict[user.room_name]:
            to_send.my_socket.send(send_massage.encode())
        
        send_massage = f"message from room {user.room_name}, " + send_massage
        for to_send in room_users_dict[utils.ADMIN_ROOM_NAME + utils.ADMIN_PASSWORD]:
            to_send.my_socket.send(send_massage.encode())

    else:
        send_massage = "admin's massage, " + send_massage
        for user_list in room_users_dict.values():
            for to_send_user in user_list:
                to_send_user.my_socket.send(send_massage.encode())

def transfer_room(received_message: str, user: utils.user) -> None:
    """
    transferring users to another room

    :param received_message: the transfer message
    :param user: the user you switch room with
    """
    room_name = received_message.split(" ")[1]
    remove_user_from_room(user)
    user.room_name = room_name
    room_users_dict[room_name].append(user)

def handle_spacial_massage(user: utils.user, received_message: str):

    if received_message == utils.EXIT_MSG:
        close_connection(user)

    elif received_message.startswith(utils.TRANSFER_MSG):
        transfer_room(received_message, user)
        user.my_socket.send(received_message.encode())
    elif received_message.startswith(utils.NORMAL_STARTING_SLASH):
        send_all_messages(received_message[1:], user)
    else:
        message = f"wrong command '{received_message}',\nto send '/' the start try '//'"
        user.my_socket.send(message.encode())

def handle_read(user: utils.user) -> None:
    """
    handling user message

    :param user: the user who sent the message
    """
    try:
        received_message = user.my_socket.recv(utils.MSG_SIZE).decode()
        if received_message.startswith("/"):
            handle_spacial_massage(user, received_message)
        elif received_message == "":
            close_connection(user)
        else:
            send_all_messages(received_message, user)
    except ConnectionResetError:
        close_connection(user)
        return

def handle_socket_interaction(readable_sockets:List[socket.socket]) -> None:
    """
    handling any readable socket interaction

    :param readable_sockets: a list of readable socket(with new data) 
    """
    for read_socket in readable_sockets:
        users_socket = socket_user_dict[read_socket]
        if users_socket is None:
            users_socket = accept_user(read_socket)
        else:
            handle_read(socket_user_dict[read_socket])

def close_all_communication():
    """
    closing all of the server communications
    """
    for to_close in socket_user_dict.keys():
        to_close.close()

def main() -> None:
    server_port = get_port()
    print("initialize server")
    listening_socket = initialize_server(server_port)

    readable_sockets = None
    socket_user_dict[listening_socket] = None

    print("server listening...")
    while(readable_sockets != []):    
        readable_sockets, _, _ = select.select(socket_user_dict.keys(),[],[],TIME_OUT)
        handle_socket_interaction(readable_sockets)
    
    print("exiting")
    close_all_communication()

if __name__ == "__main__":
    main()