async def test_auser_after_alogin(self):
        self.middleware(self.request)
        auser = await self.request.auser()
        self.assertEqual(auser, self.user)
        await alogin(self.request, self.user2)
        auser_second = await self.request.auser()
        self.assertEqual(auser_second, self.user2)