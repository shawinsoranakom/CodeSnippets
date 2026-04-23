async def test_acreate(self):
        await SimpleModel.objects.acreate(field=4)
        self.assertEqual(await SimpleModel.objects.acount(), 4)