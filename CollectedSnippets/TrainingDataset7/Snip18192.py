def test_unknown_user(self):
        """
        Tests the case where the username passed in the header does not exist
        as a User.
        """
        num_users = User.objects.count()
        response = self.client.get("/remote_user/", **{self.header: "newuser"})
        self.assertEqual(response.context["user"].username, "newuser")
        self.assertEqual(User.objects.count(), num_users + 1)
        User.objects.get(username="newuser")

        # Another request with same user should not create any new users.
        response = self.client.get("/remote_user/", **{self.header: "newuser"})
        self.assertEqual(User.objects.count(), num_users + 1)