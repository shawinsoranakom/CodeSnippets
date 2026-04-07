def test_exists_union_empty_result(self):
        qs = Number.objects.filter(pk__in=[])
        self.assertIs(qs.union(qs).exists(), False)