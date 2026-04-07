async def test_actual_expiry_async(self):
        old_session_key = None
        new_session_key = None
        try:
            await self.session.aset("foo", "bar")
            await self.session.aset_expiry(-timedelta(seconds=10))
            await self.session.asave()
            old_session_key = self.session.session_key
            # With an expiry date in the past, the session expires instantly.
            new_session = self.backend(self.session.session_key)
            new_session_key = new_session.session_key
            self.assertIs(await new_session.ahas_key("foo"), False)
        finally:
            await self.session.adelete(old_session_key)
            await self.session.adelete(new_session_key)