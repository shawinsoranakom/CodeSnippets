def test_override(self):
        self.assertFalse(settings.is_overridden("ALLOWED_HOSTS"))
        with override_settings(ALLOWED_HOSTS=[]):
            self.assertTrue(settings.is_overridden("ALLOWED_HOSTS"))