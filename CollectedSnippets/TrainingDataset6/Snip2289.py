def get_stream_simple(session: SessionDep) -> Any:
    def iter_data():
        yield from ["x", "y", "z"]

    return StreamingResponse(iter_data())