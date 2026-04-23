def test_annotate(self):
        qs = Season.objects.annotate(equal=Exact(F("year"), 1942))
        self.assertCountEqual(
            qs.values_list("year", "equal"),
            ((1942, True), (1842, False), (2042, False)),
        )