async def test_custom_expiry_reset_async(self):
        await self.session.aset_expiry(None)
        await self.session.aset_expiry(10)
        await self.session.aset_expiry(None)
        self.assertEqual(
            await self.session.aget_expiry_age(), self.custom_session_cookie_age
        )