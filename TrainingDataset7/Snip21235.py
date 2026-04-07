def request_lifecycle():
            """Fake request_started/request_finished."""
            return (threading.get_ident(), id(connection))