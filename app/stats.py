import json
import time

import docker


class Stats:
    def __init__(self, contianer, delay: int = 1) -> None:
        self.container = contianer
        self.delay = delay

    def __cpu_percent(self, cpu_stats: dict, precpu_stats: dict) -> float:
        """Calculate the CPU usage percentage

        Args:
            cpu_stats (dict): dict of cpu stats
            precpu_stats (dict): dict of precpu stats

        Returns:
            float: cpu usage percentage
        """
        cpu_count = cpu_stats.get("online_cpus", 0)
        cpu_percent = 0.0
        cpu_delta = float(cpu_stats["cpu_usage"]["total_usage"]) - float(
            precpu_stats["cpu_usage"]["total_usage"]
        )
        system_delta = float(cpu_stats["system_cpu_usage"]) - float(
            precpu_stats["cpu_usage"]["total_usage"]
        )
        if system_delta > 0.0:
            cpu_percent = cpu_delta / system_delta * 100.0 * cpu_count
        return cpu_percent

    def __blkio_bytes(self, blkio_stats: dict) -> tuple[int, int]:
        """
        :param blkio_stats:
        :return: (read_bytes, wrote_bytes), ints
        """
        bytes_stats = blkio_stats.get("io_service_bytes_recursive", [])
        if not bytes_stats:
            return 0, 0
        read_bytes = 0
        write_bytes = 0
        for s in bytes_stats:
            if s["op"] == "Read":
                read_bytes += s["value"]
            elif s["op"] == "Write":
                write_bytes += s["value"]

        return read_bytes, write_bytes

    def __memory_bytes(self, memory_stats: dict) -> tuple[int, int]:
        """
        :param memory_stats:
        :return: (used_bytes, limit_bytes), ints
        """
        used_bytes = memory_stats["usage"]
        limit_bytes = memory_stats["limit"]

        return used_bytes, limit_bytes

    def __parse_stats(self, raw_stats: bytes, fields: list = None):
        if fields is None:
            fields = ["cpu_stats", "memory_stats", "networks"]

        stats = json.loads(raw_stats.decode("utf-8"))

        cpu_data = stats.get("cpu_stats", {})
        precpu_data = stats.get("precpu_stats", {})
        cpu_percent: float = self.__cpu_percent(cpu_data, precpu_data)

        memory_data: dict = stats.get("memory_stats", {})
        memory_used_bytes, memory_limit_bytes = self.__memory_bytes(memory_data)

        blkio_data: dict = stats.get("blkio_stats", {})
        blkio_read_bytes, blkio_write_bytes = self.__blkio_bytes(blkio_data)

        return {
            "cpu_percent": cpu_percent,
            "memory_used_bytes": memory_used_bytes,
            "memory_limit_bytes": memory_limit_bytes,
            "blkio_read_bytes": blkio_read_bytes,
            "blkio_write_bytes": blkio_write_bytes,
        }

    def stream_stats(self):
        for line in self.container.stats(stream=True):
            stats = self.__parse_stats(line)
            yield json.dumps(stats)


if __name__ == "__main__":
    container = "logen"
    stats = Stats(container)
    for line in stats.stream_stats():
        print(line)
