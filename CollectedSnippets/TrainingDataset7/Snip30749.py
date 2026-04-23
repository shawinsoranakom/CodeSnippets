def test_extra_values_list(self):
        # testing for ticket 14930 issues
        qs = Number.objects.extra(select={"value_plus_one": "num+1"})
        qs = qs.order_by("value_plus_one")
        qs = qs.values_list("num")
        self.assertSequenceEqual(qs, [(72,)])