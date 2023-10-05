import socket
import os
import tqdm
import threading
import time
import argparse


# Define the size of the buffer
BUFFER_SIZE = 1024

SEPARATOR = "|"

# Define the server address (host and port)
server_host = "127.0.0.1"
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
            
            # Receive the file name from the client
            try:
                received = connection.recv(BUFFER_SIZE).decode()
            except Exception as e:
                received = connection.recv(BUFFER_SIZE)
            if not received:
                break
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


def handle_client(server_socket, storageDirectory):
    try:
        while True:
            # Accept incoming connection from the client
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")
            client_thread = threading.Thread(target=receive_files, args=(client_socket, storageDirectory))
            client_thread.daemon = True
            client_thread.start()


    except KeyboardInterrupt:
        print("Thread is shutting down.")
    except Exception as e:
        print(f"Error handling client: {e}")


def main():

    storageDirectory = storage_directory()
    # storageDirectory = "received_files"

    # Create the receive directory if it doesn't exist
    if not os.path.exists(os.path.join(os.path.dirname(__file__),storageDirectory)):
        os.makedirs(os.path.join(os.path.dirname(__file__),storageDirectory))

    # Now you can use 'directory_path' in your Python code.
    print(f"Using directory: {storageDirectory}")

    
    # Create a TCP socket server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the server address
    server_socket.bind((server_host, server_port))

    # Listen for incoming connections
    server_socket.listen(5)
    print(f"Server is listening on {server_host}:{server_port}")

    # Listen for incoming connections
    try:
        t1 = threading.Thread(target=handle_client, args=(server_socket, storageDirectory))
        t1.daemon = True
        t1.start()


        while True:
            time.sleep(0)

    except KeyboardInterrupt:
        print("Thread is shutting down.")
        server_socket.close()

if __name__ == "__main__":
    main()