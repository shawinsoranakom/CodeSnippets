def test_session_key_flushed_on_login_after_password_change(self):
        """
        As above, but same user logging in after a password change.
        """
        self.login()
        original_session_key = self.client.session.session_key

        # If no password change, session key should not be flushed.
        self.login()
        self.assertEqual(original_session_key, self.client.session.session_key)

        user = User.objects.get(username="testclient")
        user.set_password("foobar")
        user.save()

        self.login(password="foobar")
        self.assertNotEqual(original_session_key, self.client.session.session_key)