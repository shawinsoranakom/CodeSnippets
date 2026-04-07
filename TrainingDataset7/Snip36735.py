def test_make_aware2(self):
        CEST = datetime.timezone(datetime.timedelta(hours=2), "CEST")
        self.assertEqual(
            timezone.make_aware(datetime.datetime(2011, 9, 1, 12, 20, 30), PARIS_ZI),
            datetime.datetime(2011, 9, 1, 12, 20, 30, tzinfo=CEST),
        )
        with self.assertRaises(ValueError):
            timezone.make_aware(
                datetime.datetime(2011, 9, 1, 12, 20, 30, tzinfo=PARIS_ZI), PARIS_ZI
            )