def test_annotated_array_subquery_with_json_objects(self):
        inner_qs = NullableIntegerArrayModel.objects.exclude(
            pk=models.OuterRef("pk")
        ).values(json=JSONObject(order="order", field="field"))
        siblings_json = (
            NullableIntegerArrayModel.objects.annotate(
                siblings_json=ArraySubquery(inner_qs),
            )
            .values_list("siblings_json", flat=True)
            .get(order=1)
        )
        self.assertSequenceEqual(
            siblings_json,
            [
                {"field": [2], "order": 2},
                {"field": [2, 3], "order": 3},
                {"field": [20, 30, 40], "order": 4},
                {"field": None, "order": 5},
            ],
        )