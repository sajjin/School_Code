import socket
import os


def connect_recive(BUFFER_SIZE, socket_path, storage_directory):
    try:
        # Create the storage directory if it doesn't exist
        if not os.path.exists(os.path.join(os.path.dirname(__file__),storage_directory)):
            os.makedirs(os.path.join(os.path.dirname(__file__),storage_directory))

        # Create a Unix domain socket server
        server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Bind the socket to the defined path
        server_socket.bind(socket_path)

        # Listen for incoming connections
        server_socket.listen(1)
        print(f"Server is listening on {socket_path}")

        try:
            while True:
                # Accept incoming connections
                connection, client_address = server_socket.accept()
                print(f"Accepted connection from {client_address}")

                try:
                    # Receive and store files from the client
                    while True:
                        # Receive the file name from the client
                        file_name = connection.recv(BUFFER_SIZE).decode('utf-8')
                        if file_name == "":
                            break
                        for sec_file in file_name.split("<>"):

                            file_detail = sec_file.split("|")
                
                            try:
                                file_name = file_detail[0]
                                file_size = int(file_detail[1])
                            except:
                                break


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
                            with open(file_path, 'wb') as file:
                                received_data = 0
                                while received_data < file_size:
                                    data = file_detail[2].encode('utf-8')
                                    if not data:
                                        break
                                    file.write(data)
                                    received_data += len(data)
                                print(f"Received and saved file: {file_name}")

                finally:
                    # Clean up the connection
                    connection.close()

        except KeyboardInterrupt:
            # Handle Ctrl-C to gracefully exit the server
            print("Server is shutting down.")
            server_socket.close()
            os.unlink(socket_path)
    except Exception as e:
        print(f"Error: {e}")
        server_socket.close()
        os.unlink(socket_path)




def main():
    BUFFER_SIZE = 1024 * 100

    # Define the path to the Unix domain socket
    socket_path = "/tmp/my_unix_socket"

    # Define the directory where files will be stored
    storage_directory = "server_storage"

    connect_recive(BUFFER_SIZE, socket_path, storage_directory)



if __name__ == "__main__":
    main()