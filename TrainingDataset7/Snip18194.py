def test_known_user(self):
        """
        Tests the case where the username passed in the header is a valid User.
        """
        User.objects.create(username="knownuser")
        User.objects.create(username="knownuser2")
        num_users = User.objects.count()
        response = self.client.get("/remote_user/", **{self.header: self.known_user})
        self.assertEqual(response.context["user"].username, "knownuser")
        self.assertEqual(User.objects.count(), num_users)
        # A different user passed in the headers causes the new user
        # to be logged in.
        response = self.client.get("/remote_user/", **{self.header: self.known_user2})
        self.assertEqual(response.context["user"].username, "knownuser2")
        self.assertEqual(User.objects.count(), num_users)