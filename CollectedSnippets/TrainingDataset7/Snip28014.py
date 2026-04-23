def test_key_transform_raw_expression(self):
        expr = RawSQL(self.raw_sql, ['{"x": "bar"}'])
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__foo=KeyTransform("x", expr)),
            [self.objs[7]],
        )