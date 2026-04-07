def test_extra_values_order_multiple(self):
        # Postgres doesn't allow constants in order by, so check for that.
        qs = Number.objects.extra(
            select={
                "value_plus_one": "num+1",
                "value_minus_one": "num-1",
                "constant_value": "1",
            }
        )
        qs = qs.order_by("value_plus_one", "value_minus_one", "constant_value")
        qs = qs.values("num")
        self.assertSequenceEqual(qs, [{"num": 72}])