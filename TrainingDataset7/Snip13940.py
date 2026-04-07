def _create_server(self, connections_override=None):
        return self.server_class(
            (self.host, self.port),
            QuietWSGIRequestHandler,
            allow_reuse_address=False,
            connections_override=connections_override,
        )