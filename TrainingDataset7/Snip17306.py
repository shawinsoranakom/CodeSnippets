def test_empty_dunder_path_fallback_to_dunder_file(self):
        """If the __path__ attr is empty, use __file__ if set."""
        ac = AppConfig("label", Stub(__path__=[], __file__="b/__init__.py"))

        self.assertEqual(ac.path, "b")