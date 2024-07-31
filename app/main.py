# Uncomment this to pass the first stage
import socket


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    conn, _addr = server_socket.accept()

    content = conn.recv(1024).decode()

    is_pure_path = content[content.find("/") + 1] == " "

    if is_pure_path:
        conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
    else:
        conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

    conn.close()


if __name__ == "__main__":
    main()
