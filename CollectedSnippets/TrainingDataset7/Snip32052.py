def test_unevaluated_lazysettings_repr(self):
        lazy_settings = LazySettings()
        expected = "<LazySettings [Unevaluated]>"
        self.assertEqual(repr(lazy_settings), expected)