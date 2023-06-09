import docker
from docker import DockerClient


class Logs:
    def __init__(self, container) -> None:
        self.container = container

    def stream_logs(self, delay: int = 1):
        for line in self.container.logs(stream=True, follow=True, tail=delay):
            yield line.decode("utf-8").strip()


if __name__ == "__main__":
    log_stream = Logs("logen")
    for log in log_stream.stream_logs():
        print(log)
