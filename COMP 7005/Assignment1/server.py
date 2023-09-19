import socket
import os
import tqdm

# Define the size of the buffer
BUFFER_SIZE = 1024

SEPARATOR = "|"

# Define the path to the Unix domain socket
socket_path = "/tmp/my_unix_socket"

# Define the server address (host and port)
server_host = "127.0.0.1"
server_port = 12345

# Define the directory where files will be stored
storage_directory = "server_storage"

# Create the storage directory if it doesn't exist
if not os.path.exists(os.path.join(os.path.dirname(__file__),storage_directory)):
    os.makedirs(os.path.join(os.path.dirname(__file__),storage_directory))


def receive_files(connection):

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
            original_file_name = file_name
            file_counter = 1
            while True:
                file_path = os.path.join(os.path.dirname(__file__), storage_directory, file_name)
                if not os.path.exists(file_path):
                    break
                base_name, extension = os.path.splitext(original_file_name)
                file_name = f"{base_name}_{file_counter}{extension}"
                file_counter += 1
            file_path = os.path.join(os.path.dirname(__file__), storage_directory, file_name)


            # Receive the size of the file from the client
            print(f"Receiving file: {file_name} ({file_size} bytes)")


            # Receive and save the file data
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


    except KeyboardInterrupt:
        # Handle Ctrl-C to gracefully exit the server
        print("Server is shutting down.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up the connection
        connection.close()



def main():
    # Create a TCP socket server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the server address
    server_socket.bind((server_host, server_port))

    # Listen for incoming connections
    server_socket.listen(1)

    try:
        while True:
            # Accept incoming connection from the client
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")

            # Receive and save files from the client
            receive_files(client_socket)

    except KeyboardInterrupt:
        # Handle Ctrl-C to gracefully exit the server
        print("Server is shutting down.")
        server_socket.close()



if __name__ == "__main__":
    main()