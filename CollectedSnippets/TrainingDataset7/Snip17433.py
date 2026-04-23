async def test_aset(self):
        await self.mtm1.simples.aset([self.s1])
        self.assertEqual(await self.mtm1.simples.aget(), self.s1)
        await self.mtm1.simples.aset([])
        self.assertEqual(await self.mtm1.simples.acount(), 0)
        await self.mtm1.simples.aset([self.s1], clear=True)
        self.assertEqual(await self.mtm1.simples.aget(), self.s1)