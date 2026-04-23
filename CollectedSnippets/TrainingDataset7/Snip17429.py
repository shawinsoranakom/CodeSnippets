async def test_aadd(self):
        await self.mtm1.simples.aadd(self.s1)
        self.assertEqual(await self.mtm1.simples.aget(), self.s1)