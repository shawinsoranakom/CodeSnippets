def check_settings(self):
        """Assert that settings for these tests aren't present."""
        self.assertFalse(hasattr(settings, "SETTING_BOTH"))
        self.assertFalse(hasattr(settings, "SETTING_ENTER"))
        self.assertFalse(hasattr(settings, "SETTING_EXIT"))
        self.assertFalse(hasattr(settings, "SETTING_PASS"))