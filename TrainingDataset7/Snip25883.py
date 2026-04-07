def test_combined_annotated_lookups_in_filter(self):
        expression = Exact(F("year"), 1942) | GreaterThan(F("year"), 1942)
        qs = Season.objects.annotate(gte=expression).filter(gte=True)
        self.assertCountEqual(qs, [self.s1, self.s3])