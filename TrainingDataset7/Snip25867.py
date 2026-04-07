def test_annotate_field_greater_than_value(self):
        qs = Season.objects.annotate(greater=GreaterThan(F("year"), Value(1930)))
        self.assertCountEqual(
            qs.values_list("year", "greater"),
            ((1942, True), (1842, False), (2042, True)),
        )