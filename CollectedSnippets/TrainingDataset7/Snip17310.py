def test_multiple_dunder_path_no_dunder_file(self):
        """If the __path__ attr is length>1 and there is no __file__, raise."""
        with self.assertRaises(ImproperlyConfigured):
            AppConfig("label", Stub(__path__=["a", "b"]))