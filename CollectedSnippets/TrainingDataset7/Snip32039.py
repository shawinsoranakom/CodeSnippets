def tearDown(self):
        signals.COMPLEX_OVERRIDE_SETTINGS = self.old_warn_override_settings
        self.assertNotIn("TEST_WARN", signals.COMPLEX_OVERRIDE_SETTINGS)