def test_path_set_explicitly(self):
        """If subclass sets path as class attr, no module attributes needed."""

        class MyAppConfig(AppConfig):
            path = "foo"

        ac = MyAppConfig("label", Stub())

        self.assertEqual(ac.path, "foo")