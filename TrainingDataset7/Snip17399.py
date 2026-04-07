async def test_aiterator_prefetch_related(self):
        results = []
        async for s in SimpleModel.objects.prefetch_related(
            Prefetch("relatedmodel_set", to_attr="prefetched_relatedmodel")
        ).aiterator():
            results.append(s.prefetched_relatedmodel)
        self.assertCountEqual(results, [[self.r1], [self.r2], [self.r3]])