def test_no_dunder_path_fallback_to_dunder_file(self):
        """If there is no __path__ attr, use __file__."""
        ac = AppConfig("label", Stub(__file__="b/__init__.py"))

        self.assertEqual(ac.path, "b")