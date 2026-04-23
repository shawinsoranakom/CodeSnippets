def test_lookup_in_filter(self):
        qs = Season.objects.filter(GreaterThan(F("year"), 1910))
        self.assertCountEqual(qs, [self.s1, self.s3])