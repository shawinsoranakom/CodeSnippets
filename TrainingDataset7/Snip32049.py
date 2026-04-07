def test_configure(self):
        s = LazySettings()
        s.configure(SECRET_KEY="foo")

        self.assertTrue(s.is_overridden("SECRET_KEY"))