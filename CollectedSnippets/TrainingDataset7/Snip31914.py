async def test_get_expire_at_browser_close_async(self):
        # Tests get_expire_at_browser_close with different settings and
        # different set_expiry calls
        with override_settings(SESSION_EXPIRE_AT_BROWSER_CLOSE=False):
            await self.session.aset_expiry(10)
            self.assertIs(await self.session.aget_expire_at_browser_close(), False)

            await self.session.aset_expiry(0)
            self.assertIs(await self.session.aget_expire_at_browser_close(), True)

            await self.session.aset_expiry(None)
            self.assertIs(await self.session.aget_expire_at_browser_close(), False)

        with override_settings(SESSION_EXPIRE_AT_BROWSER_CLOSE=True):
            await self.session.aset_expiry(10)
            self.assertIs(await self.session.aget_expire_at_browser_close(), False)

            await self.session.aset_expiry(0)
            self.assertIs(await self.session.aget_expire_at_browser_close(), True)

            await self.session.aset_expiry(None)
            self.assertIs(await self.session.aget_expire_at_browser_close(), True)