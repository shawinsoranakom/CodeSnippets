def test_no_such_app(self):
        """
        Tests when INSTALLED_APPS contains an app that doesn't exist, either
        directly or via an app config.
        """
        with self.assertRaises(ImportError):
            with self.settings(INSTALLED_APPS=["there is no such app"]):
                pass
        msg = (
            "Cannot import 'there is no such app'. Check that "
            "'apps.apps.NoSuchApp.name' is correct."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            with self.settings(INSTALLED_APPS=["apps.apps.NoSuchApp"]):
                pass