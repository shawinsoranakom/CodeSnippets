def test_order_grouping_custom_decoder(self):
        NullableJSONModel.objects.create(value_custom={"a": "b"})
        qs = NullableJSONModel.objects.filter(value_custom__isnull=False)
        self.assertSequenceEqual(
            qs.values(
                "value_custom__a",
            )
            .annotate(
                count=Count("id"),
            )
            .order_by("value_custom__a"),
            [{"value_custom__a": "b", "count": 1}],
        )