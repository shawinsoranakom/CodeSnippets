def test_confirm_invalid_post(self):
        # Same as test_confirm_invalid, but trying to do a POST instead.
        url, path = self._test_confirm_start()
        path = path[:-5] + ("0" * 4) + path[-1]

        self.client.post(
            path,
            {
                "new_password1": "anewpassword",
                "new_password2": " anewpassword",
            },
        )
        # Check the password has not been changed
        u = User.objects.get(email="staffmember@example.com")
        self.assertTrue(not u.check_password("anewpassword"))