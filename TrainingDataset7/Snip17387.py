async def test_client_aforce_login(self):
        await self.client.aforce_login(self.test_user)
        request = HttpRequest()
        request.session = await self.client.asession()
        user = await aget_user(request)
        self.assertEqual(user.username, self.test_user.username)