def test_flat_values_list(self):
        self.assertQuerySetEqual(
            Person.objects.order_by("name").values_list("name", flat=True),
            ["p1", "p2"],
        )