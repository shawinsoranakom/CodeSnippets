async def test_alast(self):
        instance = await SimpleModel.objects.alast()
        self.assertEqual(instance, self.s3)

        instance = await SimpleModel.objects.filter(field=4).alast()
        self.assertIsNone(instance)