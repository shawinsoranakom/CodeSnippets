async def test_aearliest(self):
        instance = await SimpleModel.objects.aearliest("created")
        self.assertEqual(instance, self.s1)

        instance = await SimpleModel.objects.aearliest("-created")
        self.assertEqual(instance, self.s3)