async def test_alogin(self):
        request = HttpRequest()
        request.session = await self.client.asession()
        await alogin(request, self.test_user)
        user = await aget_user(request)
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, self.test_user.username)