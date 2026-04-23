def test_annotate_greater_than_or_equal_float(self):
        qs = Season.objects.annotate(greater=GreaterThanOrEqual(F("year"), 1942.1))
        self.assertCountEqual(
            qs.values_list("year", "greater"),
            ((1942, False), (1842, False), (2042, True)),
        )