def test_comparison(self):
        test_ranges = [range(0), range(0, -1), range(1, 1, 3),
                       range(1), range(5, 6), range(5, 6, 2),
                       range(5, 7, 2), range(2), range(0, 4, 2),
                       range(0, 5, 2), range(0, 6, 2)]
        test_tuples = list(map(tuple, test_ranges))

        # Check that equality of ranges matches equality of the corresponding
        # tuples for each pair from the test lists above.
        ranges_eq = [a == b for a in test_ranges for b in test_ranges]
        tuples_eq = [a == b for a in test_tuples for b in test_tuples]
        self.assertEqual(ranges_eq, tuples_eq)

        # Check that != correctly gives the logical negation of ==
        ranges_ne = [a != b for a in test_ranges for b in test_ranges]
        self.assertEqual(ranges_ne, [not x for x in ranges_eq])

        # Equal ranges should have equal hashes.
        for a in test_ranges:
            for b in test_ranges:
                if a == b:
                    self.assertEqual(hash(a), hash(b))

        # Ranges are unequal to other types (even sequence types)
        self.assertIs(range(0) == (), False)
        self.assertIs(() == range(0), False)
        self.assertIs(range(2) == [0, 1], False)

        # Huge integers aren't a problem.
        self.assertEqual(range(0, 2**100 - 1, 2),
                         range(0, 2**100, 2))
        self.assertEqual(hash(range(0, 2**100 - 1, 2)),
                         hash(range(0, 2**100, 2)))
        self.assertNotEqual(range(0, 2**100, 2),
                            range(0, 2**100 + 1, 2))
        self.assertEqual(range(2**200, 2**201 - 2**99, 2**100),
                         range(2**200, 2**201, 2**100))
        self.assertEqual(hash(range(2**200, 2**201 - 2**99, 2**100)),
                         hash(range(2**200, 2**201, 2**100)))
        self.assertNotEqual(range(2**200, 2**201, 2**100),
                            range(2**200, 2**201 + 1, 2**100))

        # Order comparisons are not implemented for ranges.
        with self.assertRaises(TypeError):
            range(0) < range(0)
        with self.assertRaises(TypeError):
            range(0) > range(0)
        with self.assertRaises(TypeError):
            range(0) <= range(0)
        with self.assertRaises(TypeError):
            range(0) >= range(0)