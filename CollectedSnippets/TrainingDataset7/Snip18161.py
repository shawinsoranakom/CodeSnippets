def test_nonexistent_backend(self):
        with self.assertRaises(ImportError):
            User.objects.with_perm(
                "auth.test",
                backend="invalid.backend.CustomModelBackend",
            )