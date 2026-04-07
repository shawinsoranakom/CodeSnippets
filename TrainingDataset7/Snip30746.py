def test_extra_values_order_in_extra(self):
        # testing for ticket 14930 issues
        qs = Number.objects.extra(
            select={"value_plus_one": "num+1", "value_minus_one": "num-1"},
            order_by=["value_minus_one"],
        )
        qs = qs.values("num")