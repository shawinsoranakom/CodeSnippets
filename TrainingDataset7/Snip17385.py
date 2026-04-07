async def test_change_password(self):
        await self.client.alogin(username="testuser", password="testpw")
        request = HttpRequest()
        request.session = await self.client.asession()

        async def auser():
            return self.test_user

        request.auser = auser
        await aupdate_session_auth_hash(request, self.test_user)
        user = await aget_user(request)
        self.assertIsInstance(user, User)