def test_make_naive_zoneinfo(self):
        self.assertEqual(
            timezone.make_naive(
                datetime.datetime(2011, 9, 1, 12, 20, 30, tzinfo=PARIS_ZI), PARIS_ZI
            ),
            datetime.datetime(2011, 9, 1, 12, 20, 30),
        )

        self.assertEqual(
            timezone.make_naive(
                datetime.datetime(2011, 9, 1, 12, 20, 30, fold=1, tzinfo=PARIS_ZI),
                PARIS_ZI,
            ),
            datetime.datetime(2011, 9, 1, 12, 20, 30, fold=1),
        )