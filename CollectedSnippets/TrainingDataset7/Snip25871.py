def test_annotate_greater_than_or_equal(self):
        qs = Season.objects.annotate(greater=GreaterThanOrEqual(F("year"), 1942))
        self.assertCountEqual(
            qs.values_list("year", "greater"),
            ((1942, True), (1842, False), (2042, True)),
        )