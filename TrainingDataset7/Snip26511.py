def test_override_settings_lazy(self):
        # The update_level_tags handler has been called at least once before
        # running this code when using @override_settings.
        settings.MESSAGE_TAGS = {constants.ERROR: "very-bad"}
        self.assertEqual(base.LEVEL_TAGS[constants.ERROR], "very-bad")