def test_nested_key_transform_raw_expression(self):
        expr = RawSQL(self.raw_sql, ['{"x": {"y": "bar"}}'])
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(
                value__foo=KeyTransform("y", KeyTransform("x", expr))
            ),
            [self.objs[7]],
        )