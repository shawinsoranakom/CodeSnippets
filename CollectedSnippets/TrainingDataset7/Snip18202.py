def test_inactive_user(self):
        User.objects.create(username="knownuser", is_active=False)
        response = self.client.get("/remote_user/", **{self.header: "knownuser"})
        self.assertTrue(response.context["user"].is_anonymous)