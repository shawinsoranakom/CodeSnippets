def test_tuple_lookup_rhs_must_have_2_elements(self):
        test_cases = itertools.product(
            (
                TupleExact,
                TupleGreaterThan,
                TupleGreaterThanOrEqual,
                TupleLessThan,
                TupleLessThanOrEqual,
            ),
            (
                [],
                [1],
                [1, 2, 3],
                (),
                (1,),
                (1, 2, 3),
            ),
        )

        for lookup_cls, rhs in test_cases:
            lookup_name = lookup_cls.lookup_name
            with self.subTest(lookup_name=lookup_name, rhs=rhs):
                with self.assertRaisesMessage(
                    ValueError,
                    f"'{lookup_name}' lookup of ('customer_code', 'company_code') "
                    "must have 2 elements",
                ):
                    lookup_cls((F("customer_code"), F("company_code")), rhs)