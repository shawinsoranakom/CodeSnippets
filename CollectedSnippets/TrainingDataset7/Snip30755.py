def test_named_values_list_without_fields(self):
        qs = Number.objects.extra(select={"num2": "num+1"}).annotate(Count("id"))
        values = qs.values_list(named=True).first()
        self.assertEqual(type(values).__name__, "Row")
        self.assertEqual(
            values._fields,
            ("num2", "id", "num", "other_num", "another_num", "id__count"),
        )
        self.assertEqual(values.num, 72)
        self.assertEqual(values.num2, 73)
        self.assertEqual(values.id__count, 1)