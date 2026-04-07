async def test_alogin(self):
        """See test_login()"""
        user = await UUIDUser.objects.acreate_user(username="uuid", password="test")
        self.assertTrue(await self.client.alogin(username="uuid", password="test"))
        session_key = await self.client.session.aget(SESSION_KEY)
        self.assertEqual(await UUIDUser.objects.aget(pk=session_key), user)