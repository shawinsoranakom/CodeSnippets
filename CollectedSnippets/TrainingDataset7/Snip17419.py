async def test_adelete(self):
        await SimpleModel.objects.filter(field=2).adelete()
        qs = [o async for o in SimpleModel.objects.all()]
        self.assertCountEqual(qs, [self.s1, self.s3])