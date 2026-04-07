def test_multiple_dunder_path_fallback_to_dunder_file(self):
        """If the __path__ attr is length>1, use __file__ if set."""
        ac = AppConfig("label", Stub(__path__=["a", "b"], __file__="c/__init__.py"))

        self.assertEqual(ac.path, "c")