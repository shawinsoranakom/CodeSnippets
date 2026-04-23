def test_union_multiple_models_with_values_list_and_datetime_annotations(self):
        gen_x = datetime(1966, 6, 6)
        Article.objects.create(name="Bellatrix", created=gen_x)
        column_names = ["name", "created", "order"]
        qs1 = Article.objects.annotate(order=Value(1)).values_list(*column_names)

        gen_y = datetime(1991, 10, 10)
        ReservedName.objects.create(name="Rigel", order=2)
        qs2 = ReservedName.objects.annotate(
            created=Cast(Value(gen_y), DateTimeField())
        ).values_list(*column_names)

        expected_result = [("Bellatrix", gen_x, 1), ("Rigel", gen_y, 2)]
        self.assertEqual(list(qs1.union(qs2).order_by("order")), expected_result)