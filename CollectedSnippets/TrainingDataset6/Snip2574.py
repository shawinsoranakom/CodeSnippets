def iter_data():
        yield json.dumps({"is_open": session.open})