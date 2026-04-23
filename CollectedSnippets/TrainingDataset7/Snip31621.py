def test_regression_10733(self):
        a = A.objects.create(name="a", lots_of_text="lots_of_text_a", a_field="a_field")
        b = B.objects.create(name="b", lots_of_text="lots_of_text_b", b_field="b_field")
        c = C.objects.create(
            name="c", lots_of_text="lots_of_text_c", is_published=True, c_a=a, c_b=b
        )
        results = C.objects.only(
            "name",
            "lots_of_text",
            "c_a",
            "c_b",
            "c_b__lots_of_text",
            "c_a__name",
            "c_b__name",
        ).select_related()
        self.assertSequenceEqual(results, [c])
        with self.assertNumQueries(0):
            qs_c = results[0]
            self.assertEqual(qs_c.name, "c")
            self.assertEqual(qs_c.lots_of_text, "lots_of_text_c")
            self.assertEqual(qs_c.c_b.lots_of_text, "lots_of_text_b")
            self.assertEqual(qs_c.c_a.name, "a")
            self.assertEqual(qs_c.c_b.name, "b")