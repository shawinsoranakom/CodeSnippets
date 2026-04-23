def test_override_change(self):
        settings.TEST = "test"
        self.assertEqual("test", settings.TEST)
        with self.settings(TEST="override"):
            self.assertEqual("override", settings.TEST)
            settings.TEST = "test2"
        self.assertEqual("test", settings.TEST)
        del settings.TEST