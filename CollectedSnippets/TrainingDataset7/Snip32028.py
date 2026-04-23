def test_settings_delete(self):
        settings.TEST = "test"
        self.assertEqual("test", settings.TEST)
        del settings.TEST
        msg = "'Settings' object has no attribute 'TEST'"
        with self.assertRaisesMessage(AttributeError, msg):
            getattr(settings, "TEST")