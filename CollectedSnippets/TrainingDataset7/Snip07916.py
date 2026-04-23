async def atest_cookie_worked(self):
        return (await self.aget(self.TEST_COOKIE_NAME)) == self.TEST_COOKIE_VALUE