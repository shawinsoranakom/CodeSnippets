def test_confirm_complete(self):
        url, path = self._test_confirm_start()
        response = self.client.post(
            path, {"new_password1": "anewpassword", "new_password2": "anewpassword"}
        )
        # Check the password has been changed
        u = User.objects.get(email="staffmember@example.com")
        self.assertTrue(u.check_password("anewpassword"))
        # The reset token is deleted from the session.
        self.assertNotIn(INTERNAL_RESET_SESSION_TOKEN, self.client.session)

        # Check we can't use the link again
        response = self.client.get(path)
        self.assertContains(response, "The password reset link was invalid")