def test_combined_lookups(self):
        expression = Exact(F("year"), 1942) | GreaterThan(F("year"), 1942)
        qs = Season.objects.annotate(gte=expression)
        self.assertCountEqual(
            qs.values_list("year", "gte"),
            ((1942, True), (1842, False), (2042, True)),
        )