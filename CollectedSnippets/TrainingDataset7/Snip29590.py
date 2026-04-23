def test_order_by_arrayagg_index(self):
        qs = (
            NullableIntegerArrayModel.objects.values("order")
            .annotate(ids=ArrayAgg("id"))
            .order_by("-ids__0")
        )
        self.assertQuerySetEqual(
            qs, [{"order": obj.order, "ids": [obj.id]} for obj in reversed(self.objs)]
        )