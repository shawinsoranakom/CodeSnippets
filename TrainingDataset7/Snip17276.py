def test_not_an_app_config(self):
        """
        Tests when INSTALLED_APPS contains a class that isn't an app config.
        """
        msg = "'apps.apps.NotAConfig' isn't a subclass of AppConfig."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            with self.settings(INSTALLED_APPS=["apps.apps.NotAConfig"]):
                pass