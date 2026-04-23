async def logs(
    lines_before: Annotated[int, Query(description="The number of logs before the timestamp or the last log")] = 0,
    lines_after: Annotated[int, Query(description="The number of logs after the timestamp")] = 0,
    timestamp: Annotated[int, Query(description="The timestamp to start getting logs from")] = 0,
):
    """Retrieve application logs with authentication required.

    SECURITY: Logs may contain sensitive information and require authentication.
    """
    global log_buffer  # noqa: PLW0602
    if log_buffer.enabled() is False:
        raise HTTPException(
            status_code=HTTPStatus.NOT_IMPLEMENTED,
            detail="Log retrieval is disabled",
        )
    if lines_after > 0 and lines_before > 0:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Cannot request logs before and after the timestamp",
        )
    if timestamp <= 0:
        if lines_after > 0:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Timestamp is required when requesting logs after the timestamp",
            )
        content = log_buffer.get_last_n(10) if lines_before <= 0 else log_buffer.get_last_n(lines_before)
    elif lines_before > 0:
        content = log_buffer.get_before_timestamp(timestamp=timestamp, lines=lines_before)
    elif lines_after > 0:
        content = log_buffer.get_after_timestamp(timestamp=timestamp, lines=lines_after)
    else:
        content = log_buffer.get_before_timestamp(timestamp=timestamp, lines=10)
    return JSONResponse(content=content)