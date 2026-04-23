async def test_atest_cookie(self):
        self.assertIs(await self.session.ahas_key(self.session.TEST_COOKIE_NAME), False)
        await self.session.aset_test_cookie()
        self.assertIs(await self.session.atest_cookie_worked(), True)
        await self.session.adelete_test_cookie()
        self.assertIs(await self.session.ahas_key(self.session.TEST_COOKIE_NAME), False)