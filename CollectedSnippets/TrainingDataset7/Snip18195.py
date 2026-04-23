async def test_known_user_async(self):
        """See test_known_user."""
        await User.objects.acreate(username="knownuser")
        await User.objects.acreate(username="knownuser2")
        num_users = await User.objects.acount()
        response = await self.async_client.get(
            "/remote_user/", **{self.header: self.known_user}
        )
        self.assertEqual(response.context["user"].username, "knownuser")
        self.assertEqual(await User.objects.acount(), num_users)
        # A different user passed in the headers causes the new user
        # to be logged in.
        response = await self.async_client.get(
            "/remote_user/", **{self.header: self.known_user2}
        )
        self.assertEqual(response.context["user"].username, "knownuser2")
        self.assertEqual(await User.objects.acount(), num_users)