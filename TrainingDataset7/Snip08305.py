def __init__(self, server, params):
        import pylibmc

        super().__init__(
            server, params, library=pylibmc, value_not_found_exception=pylibmc.NotFound
        )