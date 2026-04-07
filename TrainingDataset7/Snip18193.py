async def test_unknown_user_async(self):
        """See test_unknown_user."""
        num_users = await User.objects.acount()
        response = await self.async_client.get(
            "/remote_user/", **{self.header: "newuser"}
        )
        self.assertEqual(response.context["user"].username, "newuser")
        self.assertEqual(await User.objects.acount(), num_users + 1)
        await User.objects.aget(username="newuser")

        # Another request with same user should not create any new users.
        response = await self.async_client.get(
            "/remote_user/", **{self.header: "newuser"}
        )
        self.assertEqual(await User.objects.acount(), num_users + 1)