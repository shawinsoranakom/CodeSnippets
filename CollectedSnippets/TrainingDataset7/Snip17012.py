def test_coalesced_empty_result_set(self):
        with self.assertNumQueries(0):
            self.assertEqual(
                Publisher.objects.none().aggregate(
                    sum_awards=Coalesce(Sum("num_awards"), 0),
                )["sum_awards"],
                0,
            )
        # Multiple expressions.
        with self.assertNumQueries(0):
            self.assertEqual(
                Publisher.objects.none().aggregate(
                    sum_awards=Coalesce(Sum("num_awards"), None, 0),
                )["sum_awards"],
                0,
            )
        # Nested coalesce.
        with self.assertNumQueries(0):
            self.assertEqual(
                Publisher.objects.none().aggregate(
                    sum_awards=Coalesce(Coalesce(Sum("num_awards"), None), 0),
                )["sum_awards"],
                0,
            )
        # Expression coalesce.
        with self.assertNumQueries(1):
            self.assertIsInstance(
                Store.objects.none().aggregate(
                    latest_opening=Coalesce(
                        Max("original_opening"),
                        RawSQL("CURRENT_TIMESTAMP", []),
                    ),
                )["latest_opening"],
                datetime.datetime,
            )