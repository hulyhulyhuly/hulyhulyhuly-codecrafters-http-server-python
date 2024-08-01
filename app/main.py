# Uncomment this to pass the first stage
import socket
import re


class ResponseStatus:
    OK_200 = b"HTTP/1.1 200 OK\r\n\r\n"
    OK_200_with_body = (
        lambda data: f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(data)}\r\n\r\n{data}".encode()
    )
    NOT_FOUND_404 = b"HTTP/1.1 404 Not Found\r\n\r\n"


def main() -> None:
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    conn, _addr = server_socket.accept()

    content = conn.recv(1024).decode()

    """
    [0] -> Method
    [1] -> Path
    [2] -> Http's Version
    """
    # print(content)
    path = content.split(" ")[1] or None

    rule = "/echo/(.*)"

    result = re.search(rule, path, re.I)

    if path == "/":
        conn.sendall(ResponseStatus.OK_200)
    elif result:
        res = ResponseStatus.OK_200_with_body(result.group(1))
        conn.sendall(res)
    else:
        conn.sendall(ResponseStatus.NOT_FOUND_404)

    conn.close()


# HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n\r\nabc


def re_demo() -> None:
    rules = [
        "/",
        "/echo/(.*)",
    ]

    path = "/echo/abc/s"

    # for _, rule in enumerate(rules):
    #     result =

    #     if result is not None:
    #         print(result.group(1))


if __name__ == "__main__":
    main()
    # re_demo()
