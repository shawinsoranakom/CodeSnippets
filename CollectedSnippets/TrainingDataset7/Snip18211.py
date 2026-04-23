def test_unknown_user(self):
        """
        The unknown user created should be configured with an email address
        provided in the request header.
        """
        num_users = User.objects.count()
        response = self.client.get(
            "/remote_user/",
            **{
                self.header: "newuser",
                self.email_header: "user@example.com",
            },
        )
        self.assertEqual(response.context["user"].username, "newuser")
        self.assertEqual(response.context["user"].email, "user@example.com")
        self.assertEqual(response.context["user"].last_name, "")
        self.assertEqual(User.objects.count(), num_users + 1)
        newuser = User.objects.get(username="newuser")
        self.assertEqual(newuser.email, "user@example.com")