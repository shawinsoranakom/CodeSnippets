async def test_aadd(self):
        bacon = await Vegetable.objects.acreate(name="Bacon", is_yucky=False)
        t1 = await TaggedItem.objects.acreate(content_object=self.quartz, tag="shiny")
        t2 = await TaggedItem.objects.acreate(content_object=self.quartz, tag="fatty")
        await bacon.tags.aadd(t1, t2, bulk=False)
        self.assertEqual(await bacon.tags.acount(), 2)