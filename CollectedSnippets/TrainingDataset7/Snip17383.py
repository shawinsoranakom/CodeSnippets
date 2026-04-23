async def test_alogout(self):
        await self.client.alogin(username="testuser", password="testpw")
        request = HttpRequest()
        request.session = await self.client.asession()
        await alogout(request)
        user = await aget_user(request)
        self.assertIsInstance(user, AnonymousUser)