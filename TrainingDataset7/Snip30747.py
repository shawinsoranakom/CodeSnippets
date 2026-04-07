def test_extra_select_params_values_order_in_extra(self):
        # testing for 23259 issue
        qs = Number.objects.extra(
            select={"value_plus_x": "num+%s"},
            select_params=[1],
            order_by=["value_plus_x"],
        )
        qs = qs.filter(num=72)
        qs = qs.values("num")
        self.assertSequenceEqual(qs, [{"num": 72}])