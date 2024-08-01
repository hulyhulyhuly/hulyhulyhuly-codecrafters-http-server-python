import re
import socket
import threading


class ResponseStatus:
    OK_200 = b"HTTP/1.1 200 OK\r\n\r\n"

    def OK_200_with_body(data: str) -> bytes:
        response = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: text/plain\r\n"
            f"Content-Length: {len(data)}\r\n\r\n"
            f"{data}"
        )
        return response.encode()

    def OK_200_with_user_agent(user_agent: str) -> bytes:
        response = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: text/plain\r\n"
            f"Content-Length: {len(user_agent)}\r\n\r\n"
            f"{user_agent}"
        )
        return response.encode()

    NOT_FOUND_404 = b"HTTP/1.1 404 Not Found\r\n\r\n"


def server_thread(conn, _addr):
    content = conn.recv(1024).decode()

    """
    [0] -> Method
    [1] -> Path
    [2] -> Http's Version
    """
    contents = content.split(" ")
    path = contents[1] or None

    rule_user_agent = "User-Agent: (.*)\r\n"
    result_user_agent = re.search(rule_user_agent, content)

    rule_echo = "/echo/(.*)"
    result_echo = re.search(rule_echo, path)

    if path == "/":
        conn.sendall(ResponseStatus.OK_200)
    elif result_user_agent:
        res = ResponseStatus.OK_200_with_user_agent(result_user_agent.group(1))
        conn.sendall(res)
    elif result_echo:
        res = ResponseStatus.OK_200_with_body(result_echo.group(1))
        conn.sendall(res)
    else:
        conn.sendall(ResponseStatus.NOT_FOUND_404)

    conn.close()


def main() -> None:
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    server_socket.listen()

    try:
        while True:
            conn, _addr = server_socket.accept()
            threading.Thread(target=server_thread, args=(conn, _addr)).start()
    except KeyboardInterrupt:
        print("Server is shutting down...")
    finally:
        server_socket.close()
        print("Server has been shut down.")


if __name__ == "__main__":
    main()
