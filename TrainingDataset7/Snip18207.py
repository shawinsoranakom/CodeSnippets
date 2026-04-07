async def test_inactive_user_async(self):
        user = await User.objects.acreate(username="knownuser", is_active=False)
        response = await self.async_client.get(
            "/remote_user/", **{self.header: self.known_user}
        )
        self.assertEqual(response.context["user"].username, user.username)