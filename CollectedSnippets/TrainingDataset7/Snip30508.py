def test_union_multiple_models_with_values_and_datetime_annotations(self):
        gen_x = datetime(1966, 6, 6)
        Article.objects.create(name="Bellatrix", created=gen_x)
        column_names = ["name", "created", "order"]
        qs1 = Article.objects.values(*column_names, order=Value(1))

        gen_y = datetime(1991, 10, 10)
        ReservedName.objects.create(name="Rigel", order=2)
        qs2 = ReservedName.objects.values(
            *column_names, created=Cast(Value(gen_y), DateTimeField())
        )

        expected_result = [
            {"name": "Bellatrix", "created": gen_x, "order": 1},
            {"name": "Rigel", "created": gen_y, "order": 2},
        ]
        self.assertEqual(list(qs1.union(qs2).order_by("order")), expected_result)