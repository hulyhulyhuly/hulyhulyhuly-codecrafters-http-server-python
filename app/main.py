import argparse
import os
import re
import socket
import threading


class ResponseStatus:
    OK_200 = b"HTTP/1.1 200 OK\r\n\r\n"

    def OK_200_with_body(data: str, compressed) -> bytes:
        content_encodeing = f"Content-Encoding: {compressed}\r\n" if compressed else ""
        response = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: text/plain\r\n"
            f"{content_encodeing}"
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

    def OK_200_with_file(filename: str) -> bytes | None:
        filepath = f"{BASE_DIR}{filename}"
        if os.path.exists(filepath):
            file = open(filepath).read()
            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: application/octet-stream\r\n"
                f"Content-Length: {len(file)}\r\n\r\n"
                f"{file}"
            )
            return response.encode()
        else:
            return None

    def CREATED_201(filename: str, filecontent) -> bytes:
        filepath = f"{BASE_DIR}{filename}"
        with open(filepath, "w") as f:
            f.write(filecontent)
        return b"HTTP/1.1 201 Created\r\n\r\n"

    NOT_FOUND_404 = b"HTTP/1.1 404 Not Found\r\n\r\n"


def parse_encoding_type(accept_encoding):
    # TODO
    return ""


def server_thread(conn, _addr):
    content = conn.recv(1024).decode()

    """
    [0] -> Method
    [1] -> Path
    [2] -> Http's Version
    """
    contents = content.split(" ")
    method = contents[0]
    path = contents[1] or None

    rule_user_agent = "User-Agent: (.*)\r\n"
    result_user_agent = re.search(rule_user_agent, content)

    rule_accept_encoding = "Accept-Encoding: (.*)\r\n"
    result_accept_encoding = re.search(rule_accept_encoding, content)

    rule_echo = "/echo/(.*)"
    result_echo = re.search(rule_echo, path)

    rule_file = "/files/(.*)"
    result_file = re.search(rule_file, path)

    if method == "GET":
        if path == "/":
            conn.sendall(ResponseStatus.OK_200)
        elif path == "/user-agent":
            res = ResponseStatus.OK_200_with_user_agent(result_user_agent.group(1))
            conn.sendall(res)
        elif result_file:
            res = ResponseStatus.OK_200_with_file(result_file.group(1))
            if res:
                conn.sendall(res)
            else:
                conn.sendall(ResponseStatus.NOT_FOUND_404)
        elif result_echo:
            if result_accept_encoding:
                encodings = result_accept_encoding.group(1).split(", ")
                if "gzip" in encodings:
                    compressed = "gzip"
                else:
                    compressed = False
            else:
                compressed = False
            res = ResponseStatus.OK_200_with_body(result_echo.group(1), compressed)
            conn.sendall(res)
        else:
            conn.sendall(ResponseStatus.NOT_FOUND_404)
    elif method == "POST":
        if result_file:
            file_content = content.split("\r\n")[-1]
            res = ResponseStatus.CREATED_201(result_file.group(1), file_content)
            conn.sendall(res)
    conn.close()


def main() -> None:
    parse = argparse.ArgumentParser()
    parse.add_argument("--directory", type=str, help="Directory")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    server_socket.listen()

    global BASE_DIR
    BASE_DIR = parse.parse_args().directory

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
