async def test_acount(self):
        count = await SimpleModel.objects.acount()
        self.assertEqual(count, 3)