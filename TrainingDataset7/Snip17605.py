def test_non_string_backend(self):
        user = User.objects.create_user(self.username, "email", self.password)
        expected_message = (
            "backend must be a dotted import path string (got "
            "<class 'django.contrib.auth.backends.ModelBackend'>)."
        )
        with self.assertRaisesMessage(TypeError, expected_message):
            self.client._login(user, backend=ModelBackend)