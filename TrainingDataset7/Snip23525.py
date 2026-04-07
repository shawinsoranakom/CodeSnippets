async def test_aset(self):
        bacon = await Vegetable.objects.acreate(name="Bacon", is_yucky=False)
        fatty = await bacon.tags.acreate(tag="fatty")
        await bacon.tags.aset([fatty])
        self.assertEqual(await bacon.tags.acount(), 1)
        await bacon.tags.aset([])
        self.assertEqual(await bacon.tags.acount(), 0)
        await bacon.tags.aset([fatty], bulk=False, clear=True)
        self.assertEqual(await bacon.tags.acount(), 1)