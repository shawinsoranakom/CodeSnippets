def test_filter(self):
        json_null = NullableJSONModel.objects.create(value=JSONNull())
        sql_null = NullableJSONModel.objects.create(value=None)
        self.assertSequenceEqual(
            [json_null], NullableJSONModel.objects.filter(value=JSONNull())
        )
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__isnull=True), [sql_null]
        )