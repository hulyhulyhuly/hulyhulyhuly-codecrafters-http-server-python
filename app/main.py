import argparse
import gzip
import os
import re
import socket
import threading


class ResponseStatus:
    OK_200 = "200 OK\r\n\r\n"
    CREATED_201 = "201 Created"

    NOT_FOUND_404 = "HTTP/1.1 404 Not Found\r\n\r\n"


class HTTPResponse:
    @staticmethod
    def build_response(
        status: ResponseStatus, headers: dict, body: bytes = b""
    ) -> bytes:
        response_line = f"HTTP/1.1 {status}\r\n"
        headers_line = "".join(f"{k}: {v}\r\n" for k, v in headers.items())
        return f"{response_line}{headers_line}\r\n".encode() + body

    @staticmethod
    def ok_with_body(data: str, compressed: str = None) -> bytes:
        if compressed == "gzip":
            body = gzip.compress(data.encode())
            headers = {
                "Content-Encoding": "gzip",
                "Content-Type": "text/plain",
                "Content-Length": len(body),
            }
        else:
            body = data.encode()
            headers = {
                "Content-Type": "text/plain",
                "Content-Length": len(body),
            }
        print(body, gzip.decompress(body))
        return HTTPResponse.build_response(ResponseStatus.OK_200, headers, body)

    @staticmethod
    def ok_with_user_agent(user_agent: str) -> bytes:
        body = user_agent.encode()
        headers = {
            "Content-Type": "text/plain",
            "Content-Length": len(body),
        }
        return HTTPResponse.build_response(ResponseStatus.OK_200, headers, body)

    @staticmethod
    def ok_with_file(filepath: str) -> bytes:
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                body = f.read()
            headers = {
                "Content-Type": "application/octet-stream",
                "Content-Length": len(body),
            }
            return HTTPResponse.build_response(ResponseStatus.OK_200, headers, body)
        else:
            return HTTPResponse.not_found()

    @staticmethod
    def created(filepath: str) -> bytes:
        headers = {"Content-Length": 0}
        return HTTPResponse.build_response(ResponseStatus.CREATED_201, headers)

    @staticmethod
    def not_found() -> bytes:
        return HTTPResponse.build_response(ResponseStatus.NOT_FOUND_404, {})


def parse_encoding_type(accept_encoding: str) -> str:
    encodings = [e.strip() for e in accept_encoding.split(",")]
    if "gzip" in encodings:
        return "gzip"
    return ""


def handle_get(conn, path: str, headers: dict):
    if path == "/":
        conn.sendall(HTTPResponse.build_response(ResponseStatus.OK_200, {}))
    elif path == "/user-agent":
        user_agent = headers.get("User-Agent", "")
        conn.sendall(HTTPResponse.ok_with_user_agent(user_agent))
    elif path.startswith("/files/"):
        filename = path[len("/files/") :]
        conn.sendall(HTTPResponse.ok_with_file(os.path.join(BASE_DIR, filename)))
    elif path.startswith("/echo/"):
        data = path[len("/echo/") :]
        encoding = parse_encoding_type(headers.get("Accept-Encoding", ""))
        conn.sendall(HTTPResponse.ok_with_body(data, encoding))
    else:
        conn.sendall(HTTPResponse.not_found())


def handle_post(conn, path: str, content: str):
    if path.startswith("/files/"):
        filename = path[len("/files/") :]
        file_content = content.split("\r\n\r\n", 1)[-1]
        filepath = os.path.join(BASE_DIR, filename)
        with open(filepath, "w") as f:
            f.write(file_content)
        conn.sendall(HTTPResponse.created(filepath))
    else:
        conn.sendall(HTTPResponse.not_found())


def server_thread(conn, _addr):
    try:
        content = conn.recv(1024).decode()
        request_line, headers_alone = content.split("\r\n", 1)
        method, path, _ = request_line.split(" ")

        headers = {}

        for line in headers_alone.split("\r\n"):
            if line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

        if method == "GET":
            handle_get(conn, path, headers)
        elif method == "POST":
            handle_post(conn, path, content)
        else:
            conn.sendall(HTTPResponse.not_found())
    except Exception as e:
        print(f"Error handling request: {e}")
    finally:
        conn.close()


def main() -> None:
    parse = argparse.ArgumentParser()
    parse.add_argument("--directory", type=str, help="Directory")

    global BASE_DIR
    BASE_DIR = parse.parse_args().directory

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
