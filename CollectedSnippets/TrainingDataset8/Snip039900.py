def test_getattr_raises_exception_on_attr_dict(self, *mocks):
        """Verify that assignment to nested secrets raises TypeError."""
        with self.assertRaises(TypeError):
            self.secrets.subsection["new_secret"] = "123"

        with self.assertRaises(TypeError):
            self.secrets.subsection.new_secret = "123"