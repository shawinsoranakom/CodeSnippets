def test_tuple_lookup_names(self):
        test_cases = (
            (TupleExact, "exact"),
            (TupleGreaterThan, "gt"),
            (TupleGreaterThanOrEqual, "gte"),
            (TupleLessThan, "lt"),
            (TupleLessThanOrEqual, "lte"),
            (TupleIn, "in"),
            (TupleIsNull, "isnull"),
        )

        for lookup_class, lookup_name in test_cases:
            with self.subTest(lookup_name):
                self.assertEqual(lookup_class.lookup_name, lookup_name)