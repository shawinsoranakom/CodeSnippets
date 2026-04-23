def test_annotate_values_list_flat(self):
        """Find ages that are shared by at least two authors."""
        qs = (
            Author.objects.values_list("age", flat=True)
            .annotate(age_count=Count("age"))
            .filter(age_count__gt=1)
        )
        self.assertSequenceEqual(qs, [29])