def test_override_doesnt_leak(self):
        with self.assertRaises(AttributeError):
            getattr(settings, "TEST")
        with self.settings(TEST="override"):
            self.assertEqual("override", settings.TEST)
            settings.TEST = "test"
        with self.assertRaises(AttributeError):
            getattr(settings, "TEST")