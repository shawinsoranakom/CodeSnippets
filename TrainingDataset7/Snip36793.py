def test_unique_for_date_gets_picked_up(self):
        m = UniqueForDateModel()
        self.assertEqual(
            (
                [(UniqueForDateModel, ("id",))],
                [
                    (UniqueForDateModel, "date", "count", "start_date"),
                    (UniqueForDateModel, "year", "count", "end_date"),
                    (UniqueForDateModel, "month", "order", "end_date"),
                ],
            ),
            m._get_unique_checks(),
        )