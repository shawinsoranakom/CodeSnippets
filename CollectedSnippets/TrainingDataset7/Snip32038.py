def setUp(self):
        self.old_warn_override_settings = signals.COMPLEX_OVERRIDE_SETTINGS.copy()
        signals.COMPLEX_OVERRIDE_SETTINGS.add("TEST_WARN")