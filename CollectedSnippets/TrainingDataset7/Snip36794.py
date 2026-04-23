def test_unique_for_date_exclusion(self):
        m = UniqueForDateModel()
        self.assertEqual(
            (
                [(UniqueForDateModel, ("id",))],
                [
                    (UniqueForDateModel, "year", "count", "end_date"),
                    (UniqueForDateModel, "month", "order", "end_date"),
                ],
            ),
            m._get_unique_checks(exclude="start_date"),
        )