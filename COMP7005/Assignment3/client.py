from statemachine import StateMachine, State
import socket
import os
import tqdm
import time
import argparse

SEPARATOR = "|"

def utf8len(s):
    return len(s.encode('utf-8'))

class FileSender(StateMachine):
    # Define states
    idle = State('Idle', initial=True)
    myargs = State('Args')
    connect = State('Connect')
    sending_meta = State('Sending_Meta')
    send_data = State('Send_data')
    done = State('Done')

    # Define transitions

    get_args = idle.to(myargs)
    connection = myargs.to(connect)
    start_sending = connect.to(sending_meta)
    data_send = sending_meta.to(send_data)
    loop_send = send_data.to(sending_meta)
    finish_sending = send_data.to(done)

    sends = start_sending | data_send


    def __init__(self):
        super(FileSender, self).__init__()
        self.file_names = None
        self.client_socket = None
        self.server_host = None
        self.server_port = None
        self.file_names = None
        self.args = None
        self.file_size = None
        self.file_name = None

    def on_enter_myargs(self):
        # Create the arguments for CMD line
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--ipaddress", help="Server IP address", required=True)
        parser.add_argument("-p", "--port", help="Server port number", required=True)
        parser.add_argument("-f", "--file", help="File name", nargs='+', required=True)
        
        self.args = parser.parse_args()
        self.server_host = str(self.args.ipaddress)
        self.server_port = int(self.args.port)
        self.file_names = self.args.file

        # self.server_host = "10.0.0.137"
        # self.server_port = 12345
        # self.file_names = ["test.txt", "nothing.txt", "testing.txt"]
    

    def on_enter_connect(self):
        # Connect to the server
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_host, self.server_port))


    def on_enter_sending_meta(self):
        try:
                self.file_size = os.path.getsize(self.file_name)
                file_name_size = utf8len(self.file_name)
                file_size_size = utf8len(str(self.file_size))
                self.client_socket.send(f"{file_name_size}{SEPARATOR}{file_size_size}{SEPARATOR}".encode())
                confirmation = "NOT OK"

                while confirmation != "OK":
                    confirmation = self.client_socket.recv(1024).decode('utf-8')
                    self.client_socket.send(f"{self.file_name}{SEPARATOR}{self.file_size}".encode())
                
        except FileNotFoundError:
            print("File not found.")
        except Exception as e:
            print(f"Error: {e}")    
    
    
    def on_enter_done(self):
        self.client_socket.close()


    def on_enter_send_data(self):
        # Open the file and send its contents to the server
        progress = tqdm.tqdm(range(self.file_size), f"Sending {self.file_name}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(self.file_name, 'rb') as file:
            while True:

                data = file.read(self.file_size)
                if not data:
                    break
                self.client_socket.send(data)
                progress.update(len(data))
        if self.file_size >= 3073741824:
            time.sleep(30)
        elif self.file_size >= 1073741824:
            time.sleep(10)
        elif self.file_size >= 1000000:
            time.sleep(2)
        
        time.sleep(2)


def main():
    try:

        # Create a FileSender and start sending files
        sender = FileSender()
        sender.get_args()
        sender.connection()
        filenames = sender.file_names
        for file in filenames:
            sender.file_name = file
            if filenames[0] == file:
                sender.start_sending()
            else:
                sender.loop_send()
            sender.data_send()
        sender.finish_sending()
        
    except ConnectionRefusedError:
        print("Connection to the server failed.")
    except KeyboardInterrupt:
        print("Client stopped by user.")
        exit(0)

if __name__ == '__main__':
    main()  # Call the main function