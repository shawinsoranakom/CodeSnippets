async def test_aget(self):
        instance = await SimpleModel.objects.aget(field=1)
        self.assertEqual(instance, self.s1)