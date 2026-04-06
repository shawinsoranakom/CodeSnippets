def get_stream_session(
    function_session: SessionFuncDep, request_session: SessionRequestDep
) -> Any:
    def iter_data():
        yield json.dumps(
            {"func_is_open": function_session.open, "req_is_open": request_session.open}
        )

    return StreamingResponse(iter_data())