async def test_aupdate(self):
        await SimpleModel.objects.aupdate(field=99)
        qs = [o async for o in SimpleModel.objects.all()]
        values = [instance.field for instance in qs]
        self.assertEqual(set(values), {99})