def test_backend_path_login_without_authenticate_single_backend(self):
        user = User.objects.create_user(self.username, "email", self.password)
        self.client._login(user)
        self.assertBackendInSession(self.backend)