"""TODO: docstring"""

import socket

# TODO: docstring
__BLOCK_SIZE__: int = 1024


def netcat(host: str, content: bytes, port: int = 80) -> bytes:
    """TODO: docstring"""

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.sendall(content)
    sock.shutdown(socket.SHUT_WR)

    body = b""
    while True:
        data = sock.recv(__BLOCK_SIZE__)
        if len(data) == 0:
            break
        body += data

    sock.close()

    return body
