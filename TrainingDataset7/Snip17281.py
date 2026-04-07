def test_one_config_app(self):
        """Load an app that provides an AppConfig class."""
        with self.settings(INSTALLED_APPS=["apps.one_config_app"]):
            config = apps.get_app_config("one_config_app")
        self.assertIsInstance(config, OneConfig)