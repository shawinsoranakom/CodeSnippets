def test_count_union_empty_result(self):
        qs = Number.objects.filter(pk__in=[])
        self.assertEqual(qs.union(qs).count(), 0)