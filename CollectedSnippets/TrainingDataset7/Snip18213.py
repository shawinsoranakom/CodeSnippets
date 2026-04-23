async def test_header_disappears_async(self):
        """See test_header_disappears."""
        await User.objects.acreate(username="knownuser")
        # Known user authenticates
        response = await self.async_client.get(
            "/remote_user/", **{self.header: self.known_user}
        )
        self.assertEqual(response.context["user"].username, "knownuser")
        # Should stay logged in if the REMOTE_USER header disappears.
        response = await self.async_client.get("/remote_user/")
        self.assertFalse(response.context["user"].is_anonymous)
        self.assertEqual(response.context["user"].username, "knownuser")