import os
import socket
import select
import ipaddress
import argparse
import tqdm
from statemachine import StateMachine, State
import sys


os.chdir(os.path.dirname(os.path.abspath(__file__)))

class ServerFSM(StateMachine):
    DISCONNECTED = State('DISCONNECTED', initial=True)
    ARGS = State('ARGS')
    CONNECTING = State('CONNECTING')
    WAITING_FOR_CLIENT = State('WAITING_FOR_CLIENT')
    RECEIVING_FILE = State('RECEIVING_FILE')
    DUPLICATE = State('DUPLICATE')
    WRITE = State('WRITE')
    REMOVE_CLIENT = State('REMOVE_CLIENT')

    get_args = DISCONNECTED.to(ARGS)
    connect = ARGS.to(CONNECTING)
    multiplexing = CONNECTING.to(WAITING_FOR_CLIENT)
    receive_file = WAITING_FOR_CLIENT.to(RECEIVING_FILE)
    check_duplicate = RECEIVING_FILE.to(DUPLICATE)
    write_file = DUPLICATE.to(WRITE)
    file_received = REMOVE_CLIENT.to(WAITING_FOR_CLIENT)
    file_received2 = WRITE.to(RECEIVING_FILE)
    remove_client = RECEIVING_FILE.to(REMOVE_CLIENT)
    
    cycle = multiplexing | receive_file | file_received

    def __init__(self):
        super().__init__()
        self.server_socket = None
        self.active_clients = []
        self.client_receive_directories = {}
        self.client_socket = None
        self.file_name = None
        self.file_size = None
        self.file_path = None


    def on_enter_ARGS(self):
        # Add an argument for the directory path starting with -d
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--ipaddress", help="Server IP address", required=True, type=self.valid_ip)
        parser.add_argument("-p", "--port", help="Server port number", required=True)
        parser.add_argument("-d", "--directory", required=True, help="Directory path")

        print("Server is starting...")
        self.args = parser.parse_args()
        self.server_host = str(self.args.ipaddress)
        self.server_port = int(self.args.port)
        self.storage_directory = self.args.directory

        # self.storage_directory = "receive"
        # self.server_host = "0.0.0.0"
        # self.server_port = 12345
        self.connect()


    def valid_ip(self, ip):
        try:
            return str(ipaddress.ip_address(ip))
        except ValueError:
            raise argparse.ArgumentTypeError("Invalid IP address")


    def on_enter_CONNECTING(self):
        if not os.path.exists(self.storage_directory):
            os.makedirs(self.storage_directory)

        print(f"Server is listening on {self.server_host}:{self.server_port}")

        ip_type = socket.AF_INET if ':' not in self.server_host else socket.AF_INET6
        
        # Create a TCP socket server
        self.server_socket = socket.socket(ip_type, socket.SOCK_STREAM)

        # Bind the socket to the server address
        self.server_socket.bind((self.server_host, self.server_port))

        # Listen for incoming connections
        self.server_socket.listen(1)
        # Add the server socket to the list of active clients
        self.active_clients.append(self.server_socket)

        # Add the server socket to the dictionary of receive directories
        self.client_receive_directories[self.server_socket] = self.storage_directory
        self.cycle()


    def on_enter_WAITING_FOR_CLIENT(self):
        # Use select to handle I/O multiplexing
        readable, _, _ = select.select(self.active_clients, [], [])

        for sock in readable:
            if sock == self.server_socket:
                # Accept incoming connection from a client
                client_socket, client_address = self.server_socket.accept()
                print(f"Accepted connection from {client_address}")
                # Add the client socket to the list of active clients
                self.active_clients.append(client_socket)
                # Add the client socket to the dictionary of receive directories
                self.client_receive_directories[client_socket] = os.path.join(self.storage_directory, str(client_address))
                self.cycle()


    def on_enter_RECEIVING_FILE(self):
        # Receive file name and size from client
        self.client_socket = self.active_clients[1]
        received = self.client_socket.recv(1024).decode()
        if not received:
            self.remove_client()
            return
        file_info_size = received.split("|")
        self.client_socket.sendall(b"OK")
        try:
            received = self.client_socket.recv(int(file_info_size[0]) + int(file_info_size[1]) + 1).decode()
        except Exception:
            received = self.client_socket.recv(int(file_info_size[0]) + int(file_info_size[1]) + 1)
        self.file_name, self.file_size = received.split("|")
        # remove absolute path if there is
        self.file_name = os.path.basename(self.file_name)
        # convert to integer
        self.file_size = int(self.file_size)

        # Check for duplicate file names and handle as desired
        self.check_duplicate()


    def on_enter_REMOVE_CLIENT(self):
        self.active_clients.remove(self.client_socket)
        self.cycle()


    def on_enter_DUPLICATE(self):
        original_file_name = self.file_name
        file_counter = 1
        while True:
            file_path = os.path.join(os.path.dirname(__file__), self.storage_directory, self.file_name)
            if not os.path.exists(file_path):
                break
            base_name, extension = os.path.splitext(original_file_name)
            self.file_name = f"{base_name}_{file_counter}{extension}"
            file_counter += 1
        self.file_path = os.path.join(os.path.dirname(__file__), self.storage_directory, self.file_name)
        self.write_file()


    def on_enter_WRITE(self):
        progress = tqdm.tqdm(range(self.file_size), f"Receiving {self.file_name}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(self.file_path, 'wb') as file:
            received_data = 0
            while received_data < self.file_size:
                data = self.client_socket.recv(self.file_size)
                if not data:
                    break
                file.write(data)
                received_data += len(data)
                progress.update(len(data))
            print(f"Received and saved file: {self.file_name}")
            self.file_received2()


def main():
    try:
        fsm = ServerFSM()
        fsm.get_args()
    except KeyboardInterrupt:
        print("Server stopped by user.")
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(f"Error: {exc_type}, {e}, {exc_tb.tb_lineno}")
        exit(1)
    finally:
        fsm.server_socket.close()
        exit(0)


if __name__ == "__main__":
    main()