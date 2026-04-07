def test_known_user(self):
        """
        The strings passed in REMOTE_USER should be cleaned and the known users
        should not have been configured with an email address.
        """
        super().test_known_user()
        knownuser = User.objects.get(username="knownuser")
        knownuser2 = User.objects.get(username="knownuser2")
        self.assertEqual(knownuser.email, "")
        self.assertEqual(knownuser2.email, "")
        self.assertEqual(knownuser.last_name, "knownuser")
        self.assertEqual(knownuser2.last_name, "knownuser2")