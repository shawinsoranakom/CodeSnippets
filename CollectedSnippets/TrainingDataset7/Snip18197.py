async def test_last_login_async(self):
        """See test_last_login."""
        user = await User.objects.acreate(username="knownuser")
        # Set last_login to something so we can determine if it changes.
        default_login = datetime(2000, 1, 1)
        if settings.USE_TZ:
            default_login = default_login.replace(tzinfo=UTC)
        user.last_login = default_login
        await user.asave()

        response = await self.async_client.get(
            "/remote_user/", **{self.header: self.known_user}
        )
        self.assertNotEqual(default_login, response.context["user"].last_login)

        user = await User.objects.aget(username="knownuser")
        user.last_login = default_login
        await user.asave()
        response = await self.async_client.get(
            "/remote_user/", **{self.header: self.known_user}
        )
        self.assertEqual(default_login, response.context["user"].last_login)