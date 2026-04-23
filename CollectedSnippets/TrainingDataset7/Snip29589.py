def test_group_by_order_by_select_index(self):
        with self.assertNumQueries(1) as ctx:
            self.assertSequenceEqual(
                NullableIntegerArrayModel.objects.filter(
                    field__0__isnull=False,
                )
                .values("field__0")
                .annotate(arrayagg=ArrayAgg("id"))
                .order_by("field__0"),
                [
                    {"field__0": 1, "arrayagg": [self.objs[0].pk]},
                    {"field__0": 2, "arrayagg": [self.objs[1].pk, self.objs[2].pk]},
                    {"field__0": 20, "arrayagg": [self.objs[3].pk]},
                ],
            )
        sql = ctx[0]["sql"]
        self.assertIn("GROUP BY 1", sql)
        self.assertIn("ORDER BY 1", sql)