async def test_alatest(self):
        instance = await SimpleModel.objects.alatest("created")
        self.assertEqual(instance, self.s3)

        instance = await SimpleModel.objects.alatest("-created")
        self.assertEqual(instance, self.s1)