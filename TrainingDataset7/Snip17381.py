async def test_alogin_new_user(self):
        request = HttpRequest()
        request.session = await self.client.asession()
        await alogin(request, self.test_user)
        second_user = await User.objects.acreate_user(
            "testuser2", "test2@example.com", "testpw2"
        )
        await alogin(request, second_user)
        user = await aget_user(request)
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, second_user.username)