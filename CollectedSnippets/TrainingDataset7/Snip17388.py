async def test_client_aforce_login_backend(self):
        self.test_user.is_active = False
        await self.test_user.asave()
        await self.client.aforce_login(
            self.test_user,
            backend="django.contrib.auth.backends.AllowAllUsersModelBackend",
        )
        request = HttpRequest()
        request.session = await self.client.asession()
        user = await aget_user(request)
        self.assertEqual(user.username, self.test_user.username)