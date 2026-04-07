async def test_afirst(self):
        instance = await SimpleModel.objects.afirst()
        self.assertEqual(instance, self.s1)

        instance = await SimpleModel.objects.filter(field=4).afirst()
        self.assertIsNone(instance)