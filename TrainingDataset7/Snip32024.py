def test_context_manager(self):
        with self.assertRaises(AttributeError):
            getattr(settings, "TEST")
        override = override_settings(TEST="override")
        with self.assertRaises(AttributeError):
            getattr(settings, "TEST")
        override.enable()
        self.assertEqual("override", settings.TEST)
        override.disable()
        with self.assertRaises(AttributeError):
            getattr(settings, "TEST")