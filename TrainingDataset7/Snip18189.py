async def test_no_remote_user_async(self):
        """See test_no_remote_user."""
        num_users = await User.objects.acount()

        response = await self.async_client.get("/remote_user/")
        self.assertTrue(response.context["user"].is_anonymous)
        self.assertEqual(await User.objects.acount(), num_users)

        response = await self.async_client.get("/remote_user/", **{self.header: ""})
        self.assertTrue(response.context["user"].is_anonymous)
        self.assertEqual(await User.objects.acount(), num_users)