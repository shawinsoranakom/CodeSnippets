async def test_cycle_async(self):
        await self.session.aset("a", "c")
        await self.session.aset("b", "d")
        await self.session.asave()
        prev_key = self.session.session_key
        prev_data = list(await self.session.aitems())
        await self.session.acycle_key()
        self.assertIs(await self.session.aexists(prev_key), False)
        self.assertNotEqual(self.session.session_key, prev_key)
        self.assertEqual(list(await self.session.aitems()), prev_data)