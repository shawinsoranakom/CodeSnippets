async def test_aupdate_or_create_reverse(self):
        new_relatedmodel, created = await self.s1.relatedmodel_set.aupdate_or_create()
        self.assertIs(created, True)
        self.assertEqual(await self.s1.relatedmodel_set.acount(), 1)
        self.assertEqual(new_relatedmodel.simple, self.s1)