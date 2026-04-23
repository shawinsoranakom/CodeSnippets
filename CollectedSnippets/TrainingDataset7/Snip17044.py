def test_string_agg_order_by(self):
        order_by_test_cases = (
            (
                F("original_opening").desc(),
                "Books.com;Amazon.com;Mamma and Pappa's Books",
            ),
            (
                F("original_opening").asc(),
                "Mamma and Pappa's Books;Amazon.com;Books.com",
            ),
            (F("original_opening"), "Mamma and Pappa's Books;Amazon.com;Books.com"),
            ("original_opening", "Mamma and Pappa's Books;Amazon.com;Books.com"),
            ("-original_opening", "Books.com;Amazon.com;Mamma and Pappa's Books"),
            (
                Concat("original_opening", Value("@")),
                "Mamma and Pappa's Books;Amazon.com;Books.com",
            ),
            (
                Concat("original_opening", Value("@")).desc(),
                "Books.com;Amazon.com;Mamma and Pappa's Books",
            ),
        )
        for order_by, expected_output in order_by_test_cases:
            with self.subTest(order_by=order_by, expected_output=expected_output):
                values = Store.objects.aggregate(
                    stringagg=StringAgg("name", delimiter=Value(";"), order_by=order_by)
                )
                self.assertEqual(values, {"stringagg": expected_output})