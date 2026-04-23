def test_invalid_backend_submodule(self):
        with self.assertRaises(ImportError):
            User.objects.with_perm(
                "auth.test",
                backend="json.tool",
            )