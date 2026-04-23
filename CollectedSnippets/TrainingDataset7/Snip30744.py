def test_extra_values_order_twice(self):
        # testing for ticket 14930 issues
        qs = Number.objects.extra(
            select={"value_plus_one": "num+1", "value_minus_one": "num-1"}
        )
        qs = qs.order_by("value_minus_one").order_by("value_plus_one")
        qs = qs.values("num")
        self.assertSequenceEqual(qs, [{"num": 72}])