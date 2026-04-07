def _create_server(self, connections_override=None):
        return WSGIServer(
            (self.host, self.port), QuietWSGIRequestHandler, allow_reuse_address=False
        )