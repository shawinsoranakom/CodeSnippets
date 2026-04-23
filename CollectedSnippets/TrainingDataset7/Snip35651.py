def test_update_negated_f(self):
        DataPoint.objects.update(is_active=~F("is_active"))
        self.assertCountEqual(
            DataPoint.objects.values_list("name", "is_active"),
            [("d0", False), ("d2", False), ("d3", True)],
        )
        DataPoint.objects.update(is_active=~F("is_active"))
        self.assertCountEqual(
            DataPoint.objects.values_list("name", "is_active"),
            [("d0", True), ("d2", True), ("d3", False)],
        )