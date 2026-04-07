def test_alias(self):
        qs = Season.objects.alias(greater=GreaterThan(F("year"), 1910))
        self.assertCountEqual(qs.filter(greater=True), [self.s1, self.s3])