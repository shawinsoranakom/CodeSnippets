async def test_aset_reverse(self):
        r1 = await RelatedModel.objects.acreate()
        await self.s1.relatedmodel_set.aset([r1])
        self.assertEqual(await self.s1.relatedmodel_set.aget(), r1)
        await self.s1.relatedmodel_set.aset([])
        self.assertEqual(await self.s1.relatedmodel_set.acount(), 0)
        await self.s1.relatedmodel_set.aset([r1], bulk=False, clear=True)
        self.assertEqual(await self.s1.relatedmodel_set.aget(), r1)