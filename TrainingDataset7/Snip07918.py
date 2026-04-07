async def adelete_test_cookie(self):
        del (await self._aget_session())[self.TEST_COOKIE_NAME]