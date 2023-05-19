from logs import Logs
from stats import Stats


def merge_streams(_log: Logs, _stat: Stats):
    for log, stat in zip(_log.stream_logs(), _stat.stream_stats()):
        # yield log, stat
        yield f"data: {log}\ndata: {stat}\n\n"
