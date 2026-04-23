async def test_acontains(self):
        check = await SimpleModel.objects.acontains(self.s1)
        self.assertIs(check, True)
        # Unsaved instances are not allowed, so use an ID known not to exist.
        check = await SimpleModel.objects.acontains(
            SimpleModel(id=self.s3.id + 1, field=4)
        )
        self.assertIs(check, False)