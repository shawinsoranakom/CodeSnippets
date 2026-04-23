async def test_aclear_reverse(self):
        await RelatedModel.objects.acreate(simple=self.s1)
        self.assertEqual(await self.s1.relatedmodel_set.acount(), 1)
        await self.s1.relatedmodel_set.aclear(bulk=False)
        self.assertEqual(await self.s1.relatedmodel_set.acount(), 0)