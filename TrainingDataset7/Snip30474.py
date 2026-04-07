def test_union_all_none_slice(self):
        qs = Number.objects.filter(id__in=[])
        with self.assertNumQueries(0):
            self.assertSequenceEqual(qs.union(qs), [])
            self.assertSequenceEqual(qs.union(qs)[0:0], [])