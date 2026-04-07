def test_to_python(self):
        f = models.DecimalField(max_digits=4, decimal_places=2)
        self.assertEqual(f.to_python(3), Decimal("3"))
        self.assertEqual(f.to_python("3.14"), Decimal("3.14"))
        # to_python() converts floats and honors max_digits.
        self.assertEqual(f.to_python(3.1415926535897), Decimal("3.142"))
        self.assertEqual(f.to_python(2.4), Decimal("2.400"))
        # Uses default rounding of ROUND_HALF_EVEN.
        self.assertEqual(f.to_python(2.0625), Decimal("2.062"))
        self.assertEqual(f.to_python(2.1875), Decimal("2.188"))