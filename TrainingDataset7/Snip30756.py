def test_named_values_list_expression_with_default_alias(self):
        expr = Count("id")
        values = (
            Number.objects.annotate(id__count1=expr)
            .values_list(expr, "id__count1", named=True)
            .first()
        )
        self.assertEqual(values._fields, ("id__count2", "id__count1"))