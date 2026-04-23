async def test_header_disappears_async(self):
        """See test_header_disappears."""
        await User.objects.acreate(username="knownuser")
        # Known user authenticates
        response = await self.async_client.get(
            "/remote_user/", **{self.header: self.known_user}
        )
        self.assertEqual(response.context["user"].username, "knownuser")
        # During the session, the REMOTE_USER header disappears. Should trigger
        # logout.
        response = await self.async_client.get("/remote_user/")
        self.assertTrue(response.context["user"].is_anonymous)
        # verify the remoteuser middleware will not remove a user
        # authenticated via another backend
        await User.objects.acreate_user(username="modeluser", password="foo")
        await self.async_client.alogin(username="modeluser", password="foo")
        await aauthenticate(username="modeluser", password="foo")
        response = await self.async_client.get("/remote_user/")
        self.assertEqual(response.context["user"].username, "modeluser")