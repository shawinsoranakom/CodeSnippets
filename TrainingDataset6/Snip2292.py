def get_broken_session_stream(session: BrokenSessionDep) -> Any:
    def iter_data():
        yield from session

    return StreamingResponse(iter_data())