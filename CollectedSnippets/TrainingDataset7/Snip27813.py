def test_datetimefield_to_python_microseconds(self):
        """DateTimeField.to_python() supports microseconds."""
        f = models.DateTimeField()
        self.assertEqual(
            f.to_python("2001-01-02 03:04:05.000006"),
            datetime.datetime(2001, 1, 2, 3, 4, 5, 6),
        )
        self.assertEqual(
            f.to_python("2001-01-02 03:04:05.999999"),
            datetime.datetime(2001, 1, 2, 3, 4, 5, 999999),
        )