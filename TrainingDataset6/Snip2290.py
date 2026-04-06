def get_stream_session(session: SessionDep) -> Any:
    def iter_data():
        yield from session

    return StreamingResponse(iter_data())