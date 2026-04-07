def test_dunder_path(self):
        """
        If single element in __path__, use it (in preference to __file__).
        """
        ac = AppConfig("label", Stub(__path__=["a"], __file__="b/__init__.py"))

        self.assertEqual(ac.path, "a")