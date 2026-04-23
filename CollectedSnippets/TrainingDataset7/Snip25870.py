def test_annotate_less_than_float(self):
        qs = Season.objects.annotate(lesser=LessThan(F("year"), 1942.1))
        self.assertCountEqual(
            qs.values_list("year", "lesser"),
            ((1942, True), (1842, True), (2042, False)),
        )