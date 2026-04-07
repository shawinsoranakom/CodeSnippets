async def test_alogin_without_user(self):
        request = HttpRequest()
        request.session = await self.client.asession()
        with self.assertRaisesMessage(
            AttributeError,
            "'NoneType' object has no attribute 'get_session_auth_hash'",
        ):
            await alogin(request, None)