def test_nonupper_settings_prohibited_in_configure(self):
        s = LazySettings()
        with self.assertRaisesMessage(TypeError, "Setting 'foo' must be uppercase."):
            s.configure(foo="bar")