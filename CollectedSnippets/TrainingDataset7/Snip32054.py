def test_usersettingsholder_repr(self):
        lazy_settings = LazySettings()
        lazy_settings.configure(APPEND_SLASH=False)
        expected = "<UserSettingsHolder>"
        self.assertEqual(repr(lazy_settings._wrapped), expected)