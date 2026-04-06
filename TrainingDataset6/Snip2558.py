def get_sub(sessions: NamedSessionsDep) -> Any:
    def iter_data():
        yield json.dumps(
            {"named_session_open": sessions[0].open, "session_open": sessions[1].open}
        )

    return StreamingResponse(iter_data())