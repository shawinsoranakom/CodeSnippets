async def test_auser_after_alogout(self):
        self.middleware(self.request)
        auser = await self.request.auser()
        self.assertEqual(auser, self.user)
        await alogout(self.request)
        auser_second = await self.request.auser()
        self.assertTrue(auser_second.is_anonymous)