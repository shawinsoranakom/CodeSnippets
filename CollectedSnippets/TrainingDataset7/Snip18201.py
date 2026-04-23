async def test_user_switch_forces_new_login_async(self):
        """See test_user_switch_forces_new_login."""
        await User.objects.acreate(username="knownuser")
        # Known user authenticates
        response = await self.async_client.get(
            "/remote_user/", **{self.header: self.known_user}
        )
        self.assertEqual(response.context["user"].username, "knownuser")
        # During the session, the REMOTE_USER changes to a different user.
        response = await self.async_client.get(
            "/remote_user/", **{self.header: "newnewuser"}
        )
        # The current user is not the prior remote_user.
        # In backends that create a new user, username is "newnewuser"
        # In backends that do not create new users, it is '' (anonymous user)
        self.assertNotEqual(response.context["user"].username, "knownuser")