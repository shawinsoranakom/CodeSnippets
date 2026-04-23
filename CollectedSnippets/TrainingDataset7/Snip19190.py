def setUp(self):
        super().setUp()
        self.dirname = self.mkdtemp()
        # Caches location cannot be modified through override_settings /
        # modify_settings, hence settings are manipulated directly here and the
        # setting_changed signal is triggered manually.
        for cache_params in settings.CACHES.values():
            cache_params["LOCATION"] = self.dirname
        setting_changed.send(self.__class__, setting="CACHES", enter=False)