import socket
import argparse
import select
from typing import List
from collections import defaultdict
import utils

SERVER_IP = ""  # listening to all inputs
TIME_OUT = 60

def get_port() -> int:
        """
        getting wanted server port from the commandline
        :param return: the wanted port
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('server_port', type=int, help="the port to use as the server")
        return parser.parse_args().server_port


class Server:

    def __init__(self, port: int) -> None:

        print("initialize server")
        self._socket_user_dict = {}
        self._room_users_dict = defaultdict(list)
        self._listening_socket = self.create_listening_socket(port)
        self._socket_user_dict[self._listening_socket] = None

    def __del__(self) -> None:
        """
        closing all of the server communications
        """
        print("closing server")
        for to_close in self._socket_user_dict.keys():
            to_close.close()
    
    @staticmethod
    def create_listening_socket(port: int) -> socket.socket:
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

    def _accept_user(self) -> None:
        """
        adding new found connection and making him identify(what room and name he has)

        :param listening_socket: the socket who is open to new conversations
        """
        client_socket, address = self._listening_socket.accept()
        msg = client_socket.recv(utils.MSG_SIZE).decode()
        user_name, room_name = msg.split(" ")
        print(f"new user: {user_name} in room: {room_name}")
        curr_user = utils.user(user_name, room_name, client_socket)

        self._room_users_dict[curr_user.room_name].append(curr_user)
        self._socket_user_dict[client_socket] = curr_user

    def _remove_user_from_room(self, user : utils.user) -> None:
        """
        removing specific user from the room

        :param user: the user to remove
        """
        self._room_users_dict[user.room_name].remove(user)
        if len(self._room_users_dict[user.room_name]) == 0:
            del self._room_users_dict[user.room_name]

    def _close_connection(self, user : utils.user) -> None:
        """
        closing the connection to a certain user

        :param user: the user to close connection with
        """
        del self._socket_user_dict[user.my_socket]
        self._remove_user_from_room(user)
        user.my_socket.close()

    def _send_all_messages(self, received_massage: str, user: utils.user) -> None:
        """
        sending the user's messages to all the users in his room(and admin)
        if he is a admin sends to everyone

        :param received_massage: the message the user sent
        :param user: the user who sent the messages
        """
        send_massage = f"{user.user_name} message: {received_massage}"
        if user.room_name != (utils.ADMIN_ROOM_NAME + utils.ADMIN_PASSWORD):
            for to_send in self._room_users_dict[user.room_name]:
                to_send.my_socket.send(send_massage.encode())
            
            send_massage = f"message from room {user.room_name}, " + send_massage
            for to_send in self._room_users_dict[utils.ADMIN_ROOM_NAME + utils.ADMIN_PASSWORD]:
                to_send.my_socket.send(send_massage.encode())

        else:
            send_massage = "admin's massage, " + send_massage
            for user_list in self._room_users_dict.values():
                for to_send_user in user_list:
                    to_send_user.my_socket.send(send_massage.encode())

    def _transfer_room(self, received_message: str, user: utils.user) -> None:
        """
        transferring users to another room

        :param received_message: the transfer message
        :param user: the user you switch room with
        """
        room_name = received_message.split(" ")[1]
        print(f"user {user.user_name} switching to room {room_name}")
        self._remove_user_from_room(user)
        user.room_name = room_name
        self._room_users_dict[room_name].append(user)
        user.my_socket.send(received_message.encode())

    def _send_wrong_syntax_error(self, received_message: str, user: utils.user) -> None:
        """
        sending wrong syntax error to user

        :param received_message: the wrong command
        :param user: the user to send it to
        """
        message = f"wrong command '{received_message}',\nto send '/' the start try '//'"
        user.my_socket.send(message.encode())

    def _handle_exit_command(self, received_message: str, user: utils.user) -> None:
        """
        singing out user

        :param received_message: dont need it
        :param user: the user who asked to exit
        """
        print(f"{user.user_name} disconnecting")
        self._close_connection(user)

    def _handle_spacial_massage(self, user: utils.user, received_message: str) -> None:
        """
        handling special messages - command messages

        :param user: the user who send this messages
        :param received_message: the message(command) of the user 
        """
        handling_spacial_messages = {
            utils.EXIT_MSG: self._handle_exit_command,
            utils.TRANSFER_MSG: self._transfer_room,
        }
        command_name = received_message.split(" ")[0]
        handling_spacial_messages.get(command_name, self._send_wrong_syntax_error)(received_message, user)

    def _handle_read(self, user: utils.user) -> None:
        """
        handling user message

        :param user: the user who sent the message
        """
        try:
            received_message = user.my_socket.recv(utils.MSG_SIZE).decode()
            #normal message
            if received_message.startswith(utils.SLASH_START):
                self._send_all_messages(received_message[1:], user)
            elif received_message.startswith(utils.COMMAND_START):
                self._handle_spacial_massage(user, received_message[1:])
            elif received_message == "":
                self._close_connection(user)
            else:
                self._send_all_messages(received_message, user)
        except ConnectionResetError:
            self._close_connection(user)
            return

    def _handle_socket_interaction(self, readable_sockets:List[socket.socket]) -> None:
        """
        handling any readable socket interaction

        :param readable_sockets: a list of readable socket(with new data) 
        """
        for read_socket in readable_sockets:
            users_socket = self._socket_user_dict[read_socket]
            if not users_socket:
                users_socket = self._accept_user()
            else:
                self._handle_read(self._socket_user_dict[read_socket])
    
    def run_server(self) -> None:
        """
        running the server
        """
        print("server listening...")
        readable_sockets, _, _ = select.select(self._socket_user_dict.keys(),[],[],TIME_OUT)
    
        while readable_sockets:
            self._handle_socket_interaction(readable_sockets)
            readable_sockets, _, _ = select.select(self._socket_user_dict.keys(),[],[],TIME_OUT)

    
def main() -> None:
    main_server = Server(get_port())
    main_server.run_server()
    del main_server
    
    
        

if __name__ == "__main__":
    main()