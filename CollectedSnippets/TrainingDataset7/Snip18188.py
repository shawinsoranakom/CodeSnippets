def test_no_remote_user(self):
        """Users are not created when remote user is not specified."""
        num_users = User.objects.count()

        response = self.client.get("/remote_user/")
        self.assertTrue(response.context["user"].is_anonymous)
        self.assertEqual(User.objects.count(), num_users)

        response = self.client.get("/remote_user/", **{self.header: None})
        self.assertTrue(response.context["user"].is_anonymous)
        self.assertEqual(User.objects.count(), num_users)

        response = self.client.get("/remote_user/", **{self.header: ""})
        self.assertTrue(response.context["user"].is_anonymous)
        self.assertEqual(User.objects.count(), num_users)