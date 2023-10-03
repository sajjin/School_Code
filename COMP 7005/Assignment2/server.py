import socket
import os
import tqdm
import argparse
import select
import time


# Define the size of the buffer
BUFFER_SIZE = 500

SEPARATOR = "|"

# Define the server address (host and port)
server_host = "0.0.0.0"
server_port = 12345

def storage_directory():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="A Python script that accepts a directory path.")

    # Add an argument for the directory path starting with -d
    parser.add_argument("-d", "--directory", required=True, help="Directory path")
    # Parse the command-line arguments
    args = parser.parse_args()

    storageDirectory = args.directory
    return storageDirectory


def duplicate_files(file_name, storageDirectory):
    original_file_name = file_name
    file_counter = 1
    while True:
        file_path = os.path.join(os.path.dirname(__file__), storageDirectory, file_name)
        if not os.path.exists(file_path):
            break
        base_name, extension = os.path.splitext(original_file_name)
        file_name = f"{base_name}_{file_counter}{extension}"
        file_counter += 1
    file_path = os.path.join(os.path.dirname(__file__), storageDirectory, file_name)
    return file_path


def write_file(file_name, file_size, file_path, connection):
    progress = tqdm.tqdm(range(file_size), f"Receiving {file_name}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(file_path, 'wb') as file:
        received_data = 0
        while received_data < file_size:
            data = connection.recv(file_size)
            if not data:
                break
            file.write(data)
            received_data += len(data)
            progress.update(len(data))
        print(f"Received and saved file: {file_name}")


def receive_files(connection, storageDirectory):

    try:
        # Receive and store files from the client
        while True:
            received = connection.recv(BUFFER_SIZE).decode()
            if not received:
                break
            print(f"\n{received}\n")
            file_info_size = received.split(SEPARATOR)
            print(f"\n{file_info_size}\n")
            connection.sendall(b"OK")
            try:
                received = connection.recv(int(file_info_size[0]) + int(file_info_size[1]) + 1).decode()
            except Exception:
                received = connection.recv(int(file_info_size[0]) + int(file_info_size[1]) + 1)
            print(f"\n{received}\n")
            file_name, file_size = received.split(SEPARATOR)
            # remove absolute path if there is
            file_name = os.path.basename(file_name)
            # convert to integer
            file_size = int(file_size)

            if not file_name:
                break

            # Check for duplicate file names and handle as desired
            file_path = duplicate_files(file_name, storageDirectory)

            # Receive and save the file data
            write_file(file_name, file_size, file_path, connection)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up the connection
        connection.close()


def main():

    storageDirectory = storage_directory()
    # storageDirectory = "receive"

    # Create the receive directory if it doesn't exist
    if not os.path.exists(os.path.join(os.path.dirname(__file__),storageDirectory)):
        os.makedirs(os.path.join(os.path.dirname(__file__),storageDirectory))

    # Create a TCP socket server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the server address
    server_socket.bind((server_host, server_port))

    # Listen for incoming connections
    server_socket.listen(1)
    # Create a list to track active client sockets
    active_clients = [server_socket]

    # Create a dictionary to store receive directories for each client
    client_receive_directories = {server_socket: storageDirectory}

    try:
        while True:
            # Use select to handle I/O multiplexing
            readable, _, _ = select.select(active_clients, [], [])

            for sock in readable:
                print("loop running\n")
                if sock == server_socket:
                    print("True\n")
                    # Accept incoming connection from a client
                    client_socket, client_address = server_socket.accept()
                    print(f"Accepted connection from {client_address}")

                    # Add the client socket to the list of active clients
                    active_clients.append(client_socket)

                    # Store the receive directory in the dictionary
                    client_receive_directories[client_socket] = storageDirectory

                else:
                    print("False\n")
                    time.sleep(0.1)
                    # Handle data received from a client
                    receive_files(sock, client_receive_directories[sock])
                    active_clients.remove(sock)

    except KeyboardInterrupt:
        # Handle Ctrl-C to gracefully exit the server
        print("Server is shutting down.")
        server_socket.close()


if __name__ == "__main__":
    main()