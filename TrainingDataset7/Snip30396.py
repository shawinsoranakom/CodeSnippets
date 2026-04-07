def test_json_field_sql_null(self):
        obj = JSONFieldNullable.objects.create(json_field={})
        test_cases = [
            ("direct_none_assignment", None),
            ("value_none_assignment", Value(None)),
            (
                "expression_none_assignment",
                Coalesce(None, None, output_field=IntegerField()),
            ),
        ]
        for label, value in test_cases:
            with self.subTest(case=label):
                obj.json_field = value
                JSONFieldNullable.objects.bulk_update([obj], fields=["json_field"])
                obj.refresh_from_db()
                sql_null_qs = JSONFieldNullable.objects.filter(json_field__isnull=True)
                self.assertSequenceEqual(sql_null_qs, [obj])