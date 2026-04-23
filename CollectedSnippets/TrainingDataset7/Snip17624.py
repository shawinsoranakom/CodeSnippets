async def test_aget_user_anonymous(self):
        request = HttpRequest()
        request.session = await self.client.asession()
        user = await aget_user(request)
        self.assertIsInstance(user, AnonymousUser)