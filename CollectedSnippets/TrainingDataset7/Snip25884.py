def test_combined_annotated_lookups_in_filter_false(self):
        expression = Exact(F("year"), 1942) | GreaterThan(F("year"), 1942)
        qs = Season.objects.annotate(gte=expression).filter(gte=False)
        self.assertSequenceEqual(qs, [self.s2])