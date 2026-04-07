def test_settings_repr(self):
        module = os.environ.get(ENVIRONMENT_VARIABLE)
        lazy_settings = Settings(module)
        expected = '<Settings "%s">' % module
        self.assertEqual(repr(lazy_settings), expected)