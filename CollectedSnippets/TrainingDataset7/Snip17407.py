async def test_abulk_create(self):
        instances = [SimpleModel(field=i) for i in range(10)]
        qs = await SimpleModel.objects.abulk_create(instances)
        self.assertEqual(len(qs), 10)