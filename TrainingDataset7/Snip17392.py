async def test_adelete(self):
        await self.s1.adelete()
        count = await SimpleModel.objects.acount()
        self.assertEqual(count, 0)