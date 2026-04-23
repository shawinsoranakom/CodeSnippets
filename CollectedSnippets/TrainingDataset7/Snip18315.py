def test_confirm_invalid_hash(self):
        """A POST with an invalid token is rejected."""
        u = User.objects.get(email="staffmember@example.com")
        original_password = u.password
        url, path = self._test_confirm_start()
        path_parts = path.split("-")
        path_parts[-1] = ("0") * 20 + "/"
        path = "-".join(path_parts)

        response = self.client.post(
            path,
            {
                "new_password1": "anewpassword",
                "new_password2": "anewpassword",
            },
        )
        self.assertIs(response.context["validlink"], False)
        u.refresh_from_db()
        self.assertEqual(original_password, u.password)