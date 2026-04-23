async def test_changed_password_invalidates_aget_user(self):
        request = HttpRequest()
        request.session = await self.client.asession()
        await alogin(request, self.test_user)

        self.test_user.set_password("new_password")
        await self.test_user.asave()

        user = await aget_user(request)

        self.assertIsNotNone(user)
        self.assertTrue(user.is_anonymous)
        # Session should be flushed.
        self.assertIsNone(request.session.session_key)