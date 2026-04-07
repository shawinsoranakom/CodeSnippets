def test_last_login(self):
        """
        A user's last_login is set the first time they make a
        request but not updated in subsequent requests with the same session.
        """
        user = User.objects.create(username="knownuser")
        # Set last_login to something so we can determine if it changes.
        default_login = datetime(2000, 1, 1)
        if settings.USE_TZ:
            default_login = default_login.replace(tzinfo=UTC)
        user.last_login = default_login
        user.save()

        response = self.client.get("/remote_user/", **{self.header: self.known_user})
        self.assertNotEqual(default_login, response.context["user"].last_login)

        user = User.objects.get(username="knownuser")
        user.last_login = default_login
        user.save()
        response = self.client.get("/remote_user/", **{self.header: self.known_user})
        self.assertEqual(default_login, response.context["user"].last_login)