def test_tuple_lookup_rhs_must_be_tuple_or_list(self):
        test_cases = itertools.product(
            (
                TupleExact,
                TupleGreaterThan,
                TupleGreaterThanOrEqual,
                TupleLessThan,
                TupleLessThanOrEqual,
                TupleIn,
            ),
            (
                0,
                1,
                None,
                True,
                False,
                {"foo": "bar"},
            ),
        )

        for lookup_cls, rhs in test_cases:
            lookup_name = lookup_cls.lookup_name
            with self.subTest(lookup_name=lookup_name, rhs=rhs):
                with self.assertRaisesMessage(
                    ValueError,
                    f"'{lookup_name}' lookup of ('customer_code', 'company_code') "
                    "must be a tuple or a list",
                ):
                    lookup_cls((F("customer_code"), F("company_code")), rhs)