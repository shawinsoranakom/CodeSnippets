def test_type_error_raised(self):
        """A TypeError within a backend is propagated properly (#18171)."""
        with self.assertRaises(TypeError):
            authenticate(username="test", password="test")