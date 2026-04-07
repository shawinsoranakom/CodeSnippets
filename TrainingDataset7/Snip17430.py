async def test_aadd_reverse(self):
        r1 = await RelatedModel.objects.acreate()
        await self.s1.relatedmodel_set.aadd(r1, bulk=False)
        self.assertEqual(await self.s1.relatedmodel_set.aget(), r1)