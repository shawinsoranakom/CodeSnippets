def test_backend_path_login_with_explicit_backends(self):
        user = User.objects.create_user(self.username, "email", self.password)
        self.client._login(user, self.other_backend)
        self.assertBackendInSession(self.other_backend)