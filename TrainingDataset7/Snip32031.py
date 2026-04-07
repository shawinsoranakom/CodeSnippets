def test_override_settings_nested(self):
        """
        override_settings uses the actual _wrapped attribute at
        runtime, not when it was instantiated.
        """

        with self.assertRaises(AttributeError):
            getattr(settings, "TEST")
        with self.assertRaises(AttributeError):
            getattr(settings, "TEST2")

        inner = override_settings(TEST2="override")
        with override_settings(TEST="override"):
            self.assertEqual("override", settings.TEST)
            with inner:
                self.assertEqual("override", settings.TEST)
                self.assertEqual("override", settings.TEST2)
            # inner's __exit__ should have restored the settings of the outer
            # context manager, not those when the class was instantiated
            self.assertEqual("override", settings.TEST)
            with self.assertRaises(AttributeError):
                getattr(settings, "TEST2")

        with self.assertRaises(AttributeError):
            getattr(settings, "TEST")
        with self.assertRaises(AttributeError):
            getattr(settings, "TEST2")