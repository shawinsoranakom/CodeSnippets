async def test_aremove_reverse(self):
        r1 = await RelatedModel.objects.acreate(simple=self.s1)
        self.assertEqual(await self.s1.relatedmodel_set.acount(), 1)
        await self.s1.relatedmodel_set.aremove(r1)
        self.assertEqual(await self.s1.relatedmodel_set.acount(), 0)