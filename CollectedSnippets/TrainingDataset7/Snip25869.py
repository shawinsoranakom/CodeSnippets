def test_annotate_literal_greater_than_field(self):
        qs = Season.objects.annotate(greater=GreaterThan(1930, F("year")))
        self.assertCountEqual(
            qs.values_list("year", "greater"),
            ((1942, False), (1842, True), (2042, False)),
        )