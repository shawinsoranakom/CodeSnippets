def test_named_values_list_expression(self):
        expr = F("num") + 1
        qs = Number.objects.annotate(combinedexpression1=expr).values_list(
            expr, "combinedexpression1", named=True
        )
        values = qs.first()
        self.assertEqual(values._fields, ("combinedexpression2", "combinedexpression1"))