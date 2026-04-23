def test_aggregation_order_by_not_selected_annotation_values(self):
        result_asc = [
            self.b4.pk,
            self.b3.pk,
            self.b1.pk,
            self.b2.pk,
            self.b5.pk,
            self.b6.pk,
        ]
        result_desc = result_asc[::-1]
        tests = [
            ("min_related_age", result_asc),
            ("-min_related_age", result_desc),
            (F("min_related_age"), result_asc),
            (F("min_related_age").asc(), result_asc),
            (F("min_related_age").desc(), result_desc),
        ]
        for ordering, expected_result in tests:
            with self.subTest(ordering=ordering):
                books_qs = (
                    Book.objects.annotate(
                        min_age=Min("authors__age"),
                    )
                    .annotate(
                        min_related_age=Coalesce("min_age", "contact__age"),
                    )
                    .order_by(ordering)
                    .values_list("pk", flat=True)
                )
                self.assertEqual(list(books_qs), expected_result)