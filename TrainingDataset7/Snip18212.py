def test_header_disappears(self):
        """
        A logged in user is kept logged in even if the REMOTE_USER header
        disappears during the same browser session.
        """
        User.objects.create(username="knownuser")
        # Known user authenticates
        response = self.client.get("/remote_user/", **{self.header: self.known_user})
        self.assertEqual(response.context["user"].username, "knownuser")
        # Should stay logged in if the REMOTE_USER header disappears.
        response = self.client.get("/remote_user/")
        self.assertFalse(response.context["user"].is_anonymous)
        self.assertEqual(response.context["user"].username, "knownuser")