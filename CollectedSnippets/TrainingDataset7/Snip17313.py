def test_invalid_label(self):
        class MyAppConfig(AppConfig):
            label = "invalid.label"

        msg = "The app label 'invalid.label' is not a valid Python identifier."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            MyAppConfig("test_app", Stub())