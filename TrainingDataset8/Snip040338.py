def tearDown(self):
        config._set_option("server.scriptHealthCheckEnabled", self._old_config, "test")
        Runtime._instance = None
        super().tearDown()