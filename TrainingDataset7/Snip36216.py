def test_naive_ambiguous_datetime(self):
        # dt is ambiguous in Europe/Copenhagen.
        dt = datetime(2015, 10, 25, 2, 30, 0)

        # Try all formatters that involve self.timezone.
        self.assertEqual(format(dt, "I"), "")
        self.assertEqual(format(dt, "O"), "")
        self.assertEqual(format(dt, "T"), "")
        self.assertEqual(format(dt, "Z"), "")