def test_two_default_configs_app(self):
        """Load an app that provides two default AppConfig classes."""
        msg = (
            "'apps.two_default_configs_app.apps' declares more than one "
            "default AppConfig: 'TwoConfig', 'TwoConfigBis'."
        )
        with self.assertRaisesMessage(RuntimeError, msg):
            with self.settings(INSTALLED_APPS=["apps.two_default_configs_app"]):
                pass