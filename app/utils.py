import os

from logs import Logs
from stats import Stats


def merge_streams(_log: Logs, _stat: Stats, save: bool = False):
    for log, stat in zip(_log.stream_logs(), _stat.stream_stats()):
        yield f"{stat}|{log}"
