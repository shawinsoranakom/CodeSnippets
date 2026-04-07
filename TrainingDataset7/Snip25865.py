def test_annotate_value_greater_than_value(self):
        qs = Season.objects.annotate(greater=GreaterThan(Value(40), Value(30)))
        self.assertCountEqual(
            qs.values_list("year", "greater"),
            ((1942, True), (1842, True), (2042, True)),
        )