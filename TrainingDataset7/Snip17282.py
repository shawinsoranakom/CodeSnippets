def test_two_configs_app(self):
        """Load an app that provides two AppConfig classes."""
        with self.settings(INSTALLED_APPS=["apps.two_configs_app"]):
            config = apps.get_app_config("two_configs_app")
        self.assertIsInstance(config, AppConfig)