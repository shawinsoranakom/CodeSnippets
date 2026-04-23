def test_annotate_field_greater_than_field(self):
        qs = Season.objects.annotate(greater=GreaterThan(F("year"), F("gt")))
        self.assertCountEqual(
            qs.values_list("year", "greater"),
            ((1942, False), (1842, False), (2042, True)),
        )