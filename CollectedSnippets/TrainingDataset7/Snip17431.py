async def test_aremove(self):
        self.assertEqual(await self.mtm2.simples.acount(), 1)
        await self.mtm2.simples.aremove(self.s1)
        self.assertEqual(await self.mtm2.simples.acount(), 0)