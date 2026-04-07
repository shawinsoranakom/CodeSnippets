async def test_asave(self):
        self.s1.field = 10
        await self.s1.asave()
        refetched = await SimpleModel.objects.aget()
        self.assertEqual(refetched.field, 10)