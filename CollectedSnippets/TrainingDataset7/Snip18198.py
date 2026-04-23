def test_header_disappears(self):
        """
        A logged in user is logged out automatically when
        the REMOTE_USER header disappears during the same browser session.
        """
        User.objects.create(username="knownuser")
        # Known user authenticates
        response = self.client.get("/remote_user/", **{self.header: self.known_user})
        self.assertEqual(response.context["user"].username, "knownuser")
        # During the session, the REMOTE_USER header disappears. Should trigger
        # logout.
        response = self.client.get("/remote_user/")
        self.assertTrue(response.context["user"].is_anonymous)
        # verify the remoteuser middleware will not remove a user
        # authenticated via another backend
        User.objects.create_user(username="modeluser", password="foo")
        self.client.login(username="modeluser", password="foo")
        authenticate(username="modeluser", password="foo")
        response = self.client.get("/remote_user/")
        self.assertEqual(response.context["user"].username, "modeluser")