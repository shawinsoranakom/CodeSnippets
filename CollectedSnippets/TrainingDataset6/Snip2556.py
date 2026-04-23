def request_scope(session: SessionRequestDep) -> Any:
    def iter_data():
        yield json.dumps({"is_open": session.open})

    return StreamingResponse(iter_data())