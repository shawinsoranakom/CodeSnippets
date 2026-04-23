def test_backend_path_login_without_authenticate_multiple_backends(self):
        user = User.objects.create_user(self.username, "email", self.password)
        expected_message = (
            "You have multiple authentication backends configured and "
            "therefore must provide the `backend` argument or set the "
            "`backend` attribute on the user."
        )
        with self.assertRaisesMessage(ValueError, expected_message):
            self.client._login(user)