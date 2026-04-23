def test_in_lookup_in_filter_expression_string(self):
        self.assertCountEqual(
            Season.objects.filter(In(F("year"), [F("year"), 2042])),
            [self.s1, self.s2, self.s3],
        )