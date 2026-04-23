def test_user_password_change_updates_session(self):
        """
        #21649 - Ensure contrib.auth.views.password_change updates the user's
        session auth hash after a password change so the session isn't logged
        out.
        """
        self.login()
        original_session_key = self.client.session.session_key
        response = self.client.post(
            "/password_change/",
            {
                "old_password": "password",
                "new_password1": "password1",
                "new_password2": "password1",
            },
        )
        # if the hash isn't updated, retrieving the redirection page will fail.
        self.assertRedirects(response, "/password_change/done/")
        # The session key is rotated.
        self.assertNotEqual(original_session_key, self.client.session.session_key)