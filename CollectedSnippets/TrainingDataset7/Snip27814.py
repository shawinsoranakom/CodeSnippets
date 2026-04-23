def test_timefield_to_python_microseconds(self):
        """TimeField.to_python() supports microseconds."""
        f = models.TimeField()
        self.assertEqual(f.to_python("01:02:03.000004"), datetime.time(1, 2, 3, 4))
        self.assertEqual(f.to_python("01:02:03.999999"), datetime.time(1, 2, 3, 999999))