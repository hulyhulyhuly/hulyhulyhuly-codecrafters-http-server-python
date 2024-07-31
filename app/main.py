# Uncomment this to pass the first stage
import socket


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    conn, addr = server_socket.accept()

    conn.recv(1024)

    conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")


if __name__ == "__main__":
    main()
