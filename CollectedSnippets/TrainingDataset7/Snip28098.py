def test_case_expr_with_jsonnull_condition(self):
        obj = NullableJSONModel.objects.create(value=JSONNull())
        NullableJSONModel.objects.filter(pk=obj.pk).update(
            value=Case(
                When(
                    value=JSONNull(),
                    then=Value({"key": "replaced"}, output_field=JSONField()),
                )
            ),
        )
        obj.refresh_from_db()
        self.assertEqual(obj.value, {"key": "replaced"})