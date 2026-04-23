def test_bad_app_config(self):
        """
        Tests when INSTALLED_APPS contains an incorrect app config.
        """
        msg = "'apps.apps.BadConfig' must supply a name attribute."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            with self.settings(INSTALLED_APPS=["apps.apps.BadConfig"]):
                pass