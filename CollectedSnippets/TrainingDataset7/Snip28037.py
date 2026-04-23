def test_deep_distinct(self):
        query = NullableJSONModel.objects.distinct("value__k__l").values_list(
            "value__k__l"
        )
        expected = [("m",), (None,)]
        if not connection.features.nulls_order_largest:
            expected.reverse()
        self.assertSequenceEqual(query, expected)