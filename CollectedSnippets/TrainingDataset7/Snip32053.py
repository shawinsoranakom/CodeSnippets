def test_evaluated_lazysettings_repr(self):
        lazy_settings = LazySettings()
        module = os.environ.get(ENVIRONMENT_VARIABLE)
        expected = '<LazySettings "%s">' % module
        # Force evaluation of the lazy object.
        lazy_settings.APPEND_SLASH
        self.assertEqual(repr(lazy_settings), expected)