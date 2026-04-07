async def test_aiterator(self):
        qs = SimpleModel.objects.aiterator()
        results = []
        async for m in qs:
            results.append(m)
        self.assertCountEqual(results, [self.s1, self.s2, self.s3])