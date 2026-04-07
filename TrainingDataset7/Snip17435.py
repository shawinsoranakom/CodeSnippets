async def test_aclear(self):
        self.assertEqual(await self.mtm2.simples.acount(), 1)
        await self.mtm2.simples.aclear()
        self.assertEqual(await self.mtm2.simples.acount(), 0)