async def test_default_expiry_async(self):
        self.assertEqual(
            await self.session.aget_expiry_age(), self.custom_session_cookie_age
        )
        await self.session.aset_expiry(0)
        self.assertEqual(
            await self.session.aget_expiry_age(), self.custom_session_cookie_age
        )