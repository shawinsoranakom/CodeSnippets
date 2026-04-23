def test_float_conversion(self):

        exact_values = [0, 1, 2,
                         2**53-3,
                         2**53-2,
                         2**53-1,
                         2**53,
                         2**53+2,
                         2**54-4,
                         2**54-2,
                         2**54,
                         2**54+4]
        for x in exact_values:
            self.assertEqual(float(x), x)
            self.assertEqual(float(-x), -x)

        # test round-half-even
        for x, y in [(1, 0), (2, 2), (3, 4), (4, 4), (5, 4), (6, 6), (7, 8)]:
            for p in range(15):
                self.assertEqual(int(float(2**p*(2**53+x))), 2**p*(2**53+y))

        for x, y in [(0, 0), (1, 0), (2, 0), (3, 4), (4, 4), (5, 4), (6, 8),
                     (7, 8), (8, 8), (9, 8), (10, 8), (11, 12), (12, 12),
                     (13, 12), (14, 16), (15, 16)]:
            for p in range(15):
                self.assertEqual(int(float(2**p*(2**54+x))), 2**p*(2**54+y))

        # behaviour near extremes of floating-point range
        int_dbl_max = int(DBL_MAX)
        top_power = 2**DBL_MAX_EXP
        halfway = (int_dbl_max + top_power)//2
        self.assertEqual(float(int_dbl_max), DBL_MAX)
        self.assertEqual(float(int_dbl_max+1), DBL_MAX)
        self.assertEqual(float(halfway-1), DBL_MAX)
        self.assertRaises(OverflowError, float, halfway)
        self.assertEqual(float(1-halfway), -DBL_MAX)
        self.assertRaises(OverflowError, float, -halfway)
        self.assertRaises(OverflowError, float, top_power-1)
        self.assertRaises(OverflowError, float, top_power)
        self.assertRaises(OverflowError, float, top_power+1)
        self.assertRaises(OverflowError, float, 2*top_power-1)
        self.assertRaises(OverflowError, float, 2*top_power)
        self.assertRaises(OverflowError, float, top_power*top_power)

        for p in range(100):
            x = 2**p * (2**53 + 1) + 1
            y = 2**p * (2**53 + 2)
            self.assertEqual(int(float(x)), y)

            x = 2**p * (2**53 + 1)
            y = 2**p * 2**53
            self.assertEqual(int(float(x)), y)

        # Compare builtin float conversion with pure Python int_to_float
        # function above.
        test_values = [
            int_dbl_max-1, int_dbl_max, int_dbl_max+1,
            halfway-1, halfway, halfway + 1,
            top_power-1, top_power, top_power+1,
            2*top_power-1, 2*top_power, top_power*top_power,
        ]
        test_values.extend(exact_values)
        for p in range(-4, 8):
            for x in range(-128, 128):
                test_values.append(2**(p+53) + x)
        for value in test_values:
            self.check_float_conversion(value)
            self.check_float_conversion(-value)