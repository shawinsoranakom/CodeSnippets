def test_empty_result_optimization(self):
        with self.assertNumQueries(0):
            self.assertEqual(
                Publisher.objects.none().aggregate(
                    sum_awards=Sum("num_awards"),
                    books_count=Count("book"),
                    all_names=StringAgg("name", Value(",")),
                ),
                {
                    "sum_awards": None,
                    "books_count": 0,
                    "all_names": None,
                },
            )
        # Expression without empty_result_set_value forces queries to be
        # executed even if they would return an empty result set.
        raw_books_count = Func("book", function="COUNT")
        raw_books_count.contains_aggregate = True
        with self.assertNumQueries(1):
            self.assertEqual(
                Publisher.objects.none().aggregate(
                    sum_awards=Sum("num_awards"),
                    books_count=raw_books_count,
                ),
                {
                    "sum_awards": None,
                    "books_count": 0,
                },
            )