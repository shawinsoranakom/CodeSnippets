async def stream_logs() -> AsyncIterable[ServerSentEvent]:
    logs = [
        "2025-01-01 INFO  Application started",
        "2025-01-01 DEBUG Connected to database",
        "2025-01-01 WARN  High memory usage detected",
    ]
    for log_line in logs:
        yield ServerSentEvent(raw_data=log_line)