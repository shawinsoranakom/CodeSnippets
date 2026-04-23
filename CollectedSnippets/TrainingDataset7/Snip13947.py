def _create_server_thread(cls, connections_override):
        return cls.server_thread_class(
            cls.host,
            cls.static_handler,
            connections_override=connections_override,
            port=cls.port,
        )