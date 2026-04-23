def test_no_config_app(self):
        """Load an app that doesn't provide an AppConfig class."""
        with self.settings(INSTALLED_APPS=["apps.no_config_app"]):
            config = apps.get_app_config("no_config_app")
        self.assertIsInstance(config, AppConfig)