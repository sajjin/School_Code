import socket
import sys
import os
import tqdm
import time

# Define the server address (host and port)
socket_path = "/tmp/my_unix_socket"


def send_files(SEPARATOR, file_names, client_socket):
    try:

        for file_name in file_names:


            file_size = os.path.getsize(file_name)
            client_socket.send(f"{file_name}{SEPARATOR}{file_size}".encode())


            # Open the file and send its contents to the server
            progress = tqdm.tqdm(range(file_size), f"Sending {file_name}", unit="B", unit_scale=True, unit_divisor=1024)
            with open(file_name, 'rb') as file:
                while True:
 
                    data = file.read(file_size)
                    if not data:
                        break
                    client_socket.send(data)
                    progress.update(len(data))
            if file_size >= 3073741824:
                time.sleep(30)
            elif file_size >= 1073741824:
                time.sleep(10)
            elif file_size >= 1000000:
                time.sleep(2)
            else:
                time.sleep(1)
            
    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up the client socket
        client_socket.close()
            


# Create a Unix domain socket client

def main():
    # Define the path to the Unix domain socket
    SEPARATOR = "|"
    BUFFER_SIZE = 4096
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        # Connect to the server
        client_socket.connect(socket_path)

        # Get file names from command-line arguments
        file_names = sys.argv[1:]

        #  Send multiple files to the server
        send_files( SEPARATOR, file_names, client_socket)
    except ConnectionRefusedError:
        print("Connection to the server failed.")
    finally:
        # Clean up the client socket
        client_socket.close()


if __name__ == '__main__':
    main()  # Call the main function