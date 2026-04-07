def tearDownClass(cls):
        super().tearDownClass()
        if not issubclass(cls, TestCase) and cls._available_apps_calls_balanced > 0:
            apps.unset_available_apps()
            cls._available_apps_calls_balanced -= 1