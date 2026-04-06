def iter_data():
        yield json.dumps(
            {"func_is_open": function_session.open, "req_is_open": request_session.open}
        )