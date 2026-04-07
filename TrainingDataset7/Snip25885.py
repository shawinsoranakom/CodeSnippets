def test_lookup_in_order_by(self):
        qs = Season.objects.order_by(LessThan(F("year"), 1910), F("year"))
        self.assertSequenceEqual(qs, [self.s1, self.s3, self.s2])