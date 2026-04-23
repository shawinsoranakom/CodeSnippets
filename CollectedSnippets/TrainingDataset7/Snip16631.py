def test_password_mismatch(self):
        response = self.client.post(
            reverse("admin:auth_user_add"),
            {
                "username": "newuser",
                "password1": "newpassword",
                "password2": "mismatch",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["adminform"], "password1", [])
        self.assertFormError(
            response.context["adminform"],
            "password2",
            ["The two password fields didn’t match."],
        )