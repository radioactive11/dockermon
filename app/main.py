from fastapi import FastAPI, Response, status
from fastapi.responses import StreamingResponse
from logs import Logs
from stats import Stats
from utils import merge_streams

app = FastAPI(title="dockermon")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/stream")
def stream_controller(container: str = ""):
    if not container:
        return Response(content="container name is required", status_code=400)

    try:
        log_stream = Logs(container)
        stat_stream = Stats(container)

    except Exception as e:
        return Response(content=str(e), status_code=400)

    return StreamingResponse(
        merge_streams(log_stream, stat_stream),
        status_code=status.HTTP_200_OK,
        media_type="text/event-stream",
    )
