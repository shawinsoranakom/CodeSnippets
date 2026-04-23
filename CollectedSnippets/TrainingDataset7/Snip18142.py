def test_has_usable_password(self):
        """
        Passwords are usable even if they don't correspond to a hasher in
        settings.PASSWORD_HASHERS.
        """
        self.assertIs(User(password="some-gibbberish").has_usable_password(), True)