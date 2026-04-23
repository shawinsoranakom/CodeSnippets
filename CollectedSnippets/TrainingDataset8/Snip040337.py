def setUp(self):
        self._old_config = config.get_option("server.scriptHealthCheckEnabled")
        config._set_option("server.scriptHealthCheckEnabled", False, "test")
        super().setUp()