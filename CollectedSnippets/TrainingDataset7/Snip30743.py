def test_extra_values(self):
        # testing for ticket 14930 issues
        qs = Number.objects.extra(
            select={"value_plus_x": "num+%s", "value_minus_x": "num-%s"},
            select_params=(1, 2),
        )
        qs = qs.order_by("value_minus_x")
        qs = qs.values("num")
        self.assertSequenceEqual(qs, [{"num": 72}])