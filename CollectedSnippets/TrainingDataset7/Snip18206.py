def test_inactive_user(self):
        user = User.objects.create(username="knownuser", is_active=False)
        response = self.client.get("/remote_user/", **{self.header: self.known_user})
        self.assertEqual(response.context["user"].username, user.username)