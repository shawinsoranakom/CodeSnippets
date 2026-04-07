def test_explicit_path_overrides(self):
        """If path set as class attr, overrides __path__ and __file__."""

        class MyAppConfig(AppConfig):
            path = "foo"

        ac = MyAppConfig("label", Stub(__path__=["a"], __file__="b/__init__.py"))

        self.assertEqual(ac.path, "foo")