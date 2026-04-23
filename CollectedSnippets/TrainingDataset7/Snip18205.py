async def test_unknown_user_async(self):
        num_users = await User.objects.acount()
        response = await self.async_client.get(
            "/remote_user/", **{self.header: "newuser"}
        )
        self.assertTrue(response.context["user"].is_anonymous)
        self.assertEqual(await User.objects.acount(), num_users)