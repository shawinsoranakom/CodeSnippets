def test_override(self):
        settings.TEST = "test"
        self.assertEqual("test", settings.TEST)
        with self.settings(TEST="override"):
            self.assertEqual("override", settings.TEST)
        self.assertEqual("test", settings.TEST)
        del settings.TEST