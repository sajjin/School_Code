import socket
import sys
import os
import time

def connect_send(BUFFER_SIZE, socket_path, SEPARATOR):
    # Create a Unix domain socket client
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        # Connect to the server
        client_socket.connect(socket_path)

        # Get file names from command-line arguments
        file_names = sys.argv[1:]


        for file_name in file_names:
            # Send the file name to the server
            client_socket.sendall(file_name.encode('utf-8') + "|".encode('utf-8'))

            # Send the size of the file to the server
            file_size = os.path.getsize(file_name)
            client_socket.sendall(str(file_size).encode('utf-8') + "|".encode('utf-8'))

            # Open the file and send its contents to the server
            with open(file_name, 'rb') as file:
                while True:
                    data = file.read(BUFFER_SIZE)
                    if not data:
                        break
                    client_socket.sendall(data)
                    break
            
            client_socket.sendall(SEPARATOR.encode('utf-8'))


    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up the client socket
        time.sleep(1)
        client_socket.close()


def main():
    # Define the path to the Unix domain socket
    socket_path = "/tmp/my_unix_socket"
    SEPARATOR = "<>"
    BUFFER_SIZE = 1024 * 100
    connect_send(BUFFER_SIZE, socket_path, SEPARATOR)


if __name__ == '__main__':
    main()  # Call the main function