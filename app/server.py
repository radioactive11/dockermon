import socket
import time
from datetime import datetime

import docker
from docker import DockerClient
from logs import Logs
from loguru import logger
from stats import Stats
from utils import merge_streams


def get_container_by_name(container_name: str):
    client = docker.from_env()

    if not client.ping():
        raise Exception("Docker daemon is not running")

    try:
        container = client.containers.get(container_name)

    except docker.errors.NotFound as nfe:
        logger.error(f"Container {container_name} not found")
        return None

    return container


def parse_url(url: str) -> dict:
    """Parse the url and return a dict of the query parameters."""
    parserd_url = {}
    endpoint, query = url.split("?")

    parserd_url["endpoint"] = endpoint

    for param in query.split("&"):
        key, value = param.split("=")
        print(key, value)
        parserd_url[key] = value

    return parserd_url


def handle_request(client_socket: socket.socket, request: str):
    method, path, _ = request.split(" ", 2)

    if method != "GET":
        logger.warning(f"Unsupported method: {method}")
        response = f"HTTP/1.1 405 Method Not Allowed\r\nContent-Type: text/html\r\n\r\n {method} method is not supported"
        client_socket.sendall(response.encode())
        client_socket.close()

        return

    # Parse the path
    parsed_path = parse_url(path)
    endpoint = parsed_path.get("endpoint", "")
    container_name = parsed_path.get("container", "")

    if endpoint != "/stream" or not container_name:
        logger.warning(f"Endpoint has to be stream")
        response = f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n Only /stream with container as param is allowed"
        client_socket.sendall(response.encode())
        client_socket.close()

        return

    container = get_container_by_name(container_name)

    if not container:
        logger.warning(f"Container {container_name} not found")
        response = f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n Container {container_name} not found"
        client_socket.sendall(response.encode())
        client_socket.close()

        return

    logs = Logs(container)
    stats = Stats(container)

    try:
        for data in merge_streams(logs, stats):
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\n\r\ndata:{data}\n\n"
            client_socket.sendall(response.encode())

    except BrokenPipeError as bpe:
        logger.warning(f"Broken pipe: {bpe}")
        client_socket.close()

        return


def run_server(
    host: str = "localhost",
    port: int = 8080,
    backlog: int = 5,
    size: int = 1024,
    encoding: str = "utf-8",
):
    """Start the server."""

    socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_server.bind(("", port))

    socket_server.listen(backlog)
    logger.info(f"🏃‍♂️ Server is running  on {host}:{port}")

    while True:
        try:
            client_socket, client_address = socket_server.accept()
            logger.info(
                f"🤝 New connection from {client_address[0]}:{client_address[1]}"
            )

            request = client_socket.recv(size).decode(encoding)

            logger.debug(f"📥 Request: {request}")
            handle_request(client_socket, request)

        except KeyboardInterrupt as ki:
            logger.critical("🛑 Server stopped by user")
            socket_server.close()
            break


if __name__ == "__main__":
    run_server()
