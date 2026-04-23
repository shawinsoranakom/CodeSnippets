def test_nonupper_settings_ignored_in_default_settings(self):
        s = LazySettings()
        s.configure(SimpleNamespace(foo="bar"))
        with self.assertRaises(AttributeError):
            getattr(s, "foo")