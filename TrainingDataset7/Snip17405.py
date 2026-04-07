async def test_aget_or_create(self):
        instance, created = await SimpleModel.objects.aget_or_create(field=4)
        self.assertEqual(await SimpleModel.objects.acount(), 4)
        self.assertIs(created, True)