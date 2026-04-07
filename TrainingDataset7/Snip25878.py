def test_filter_lookup_lhs(self):
        qs = Season.objects.annotate(before_20=LessThan(F("year"), 2000)).filter(
            before_20=LessThan(F("year"), 1900),
        )
        self.assertCountEqual(qs, [self.s2, self.s3])