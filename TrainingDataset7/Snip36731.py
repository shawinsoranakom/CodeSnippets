def test_make_aware(self):
        self.assertEqual(
            timezone.make_aware(datetime.datetime(2011, 9, 1, 13, 20, 30), EAT),
            datetime.datetime(2011, 9, 1, 13, 20, 30, tzinfo=EAT),
        )
        with self.assertRaises(ValueError):
            timezone.make_aware(
                datetime.datetime(2011, 9, 1, 13, 20, 30, tzinfo=EAT), EAT
            )