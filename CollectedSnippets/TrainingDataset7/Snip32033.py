def test_no_settings_module(self):
        msg = (
            "Requested setting%s, but settings are not configured. You "
            "must either define the environment variable DJANGO_SETTINGS_MODULE "
            "or call settings.configure() before accessing settings."
        )
        orig_settings = os.environ[ENVIRONMENT_VARIABLE]
        os.environ[ENVIRONMENT_VARIABLE] = ""
        try:
            with self.assertRaisesMessage(ImproperlyConfigured, msg % "s"):
                settings._setup()
            with self.assertRaisesMessage(ImproperlyConfigured, msg % " TEST"):
                settings._setup("TEST")
        finally:
            os.environ[ENVIRONMENT_VARIABLE] = orig_settings