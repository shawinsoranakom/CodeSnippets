def test_named_values_list_with_fields(self):
        qs = Number.objects.extra(select={"num2": "num+1"}).annotate(Count("id"))
        values = qs.values_list("num", "num2", named=True).first()
        self.assertEqual(type(values).__name__, "Row")
        self.assertEqual(values._fields, ("num", "num2"))
        self.assertEqual(values.num, 72)
        self.assertEqual(values.num2, 73)