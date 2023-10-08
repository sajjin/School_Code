import socket
import sys
import os
import tqdm
import time
import argparse


def utf8len(s):
    return len(s.encode('utf-8'))

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ipadress", help="Server IP address", required=True)
    parser.add_argument("-p", "--port", help="Server port number", required=True)
    parser.add_argument("-f", "--file", help="File name", nargs='+', required=True)
    
    args = parser.parse_args()
    return args


def send_files(SEPARATOR, file_names, client_socket):
    try:

        for file_name in file_names:
            
            file_size = os.path.getsize(file_name)

            file_name_size = utf8len(file_name)
            file_size_size = utf8len(str(file_size))
            client_socket.send(f"{file_name_size}{SEPARATOR}{file_size_size}{SEPARATOR}".encode())
            confirmation = "NOT OK"

            while confirmation != "OK":
                confirmation = client_socket.recv(1024).decode('utf-8')


                client_socket.send(f"{file_name}{SEPARATOR}{file_size}".encode())
                if file_size >= 3073741824:
                    time.sleep(2)
                
                time.sleep(1)


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
            
            time.sleep(2)
            
    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up the client socket
        client_socket.close()
            



def main():
    # Define the path to the Unix domain socket
    SEPARATOR = "|"
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Get the server address and port number from the command line
    args = get_args()
    server_host = str(args.ipadress)
    server_port = int(args.port)
    file_names = args.file


    try:
        # Connect to the server
        client_socket.connect((server_host, server_port))

        # Get file names from command-line arguments
        file_names = sys.argv[1:]
        # file_names = ["test.txt", "test2.txt, test.jpeg"]
        #  Send multiple files to the server
        time.sleep(5)
        send_files( SEPARATOR, file_names, client_socket)
    except ConnectionRefusedError:
        print("Connection to the server failed.")
    finally:
        # Clean up the client socket
        client_socket.close()


if __name__ == '__main__':
    main()  # Call the main function