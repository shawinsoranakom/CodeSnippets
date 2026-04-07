async def test_cycle_with_no_session_cache_async(self):
        await self.session.aset("a", "c")
        await self.session.aset("b", "d")
        await self.session.asave()
        prev_data = await self.session.aitems()
        self.session = self.backend(self.session.session_key)
        self.assertIs(hasattr(self.session, "_session_cache"), False)
        await self.session.acycle_key()
        self.assertCountEqual(await self.session.aitems(), prev_data)