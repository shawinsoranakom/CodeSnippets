def test_unknown_user(self):
        num_users = User.objects.count()
        response = self.client.get("/remote_user/", **{self.header: "newuser"})
        self.assertTrue(response.context["user"].is_anonymous)
        self.assertEqual(User.objects.count(), num_users)