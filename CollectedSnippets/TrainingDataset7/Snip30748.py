def test_extra_multiple_select_params_values_order_by(self):
        # testing for 23259 issue
        qs = Number.objects.extra(
            select={"value_plus_x": "num+%s", "value_minus_x": "num-%s"},
            select_params=(72, 72),
        )
        qs = qs.order_by("value_minus_x")
        qs = qs.filter(num=1)
        qs = qs.values("num")
        self.assertSequenceEqual(qs, [])