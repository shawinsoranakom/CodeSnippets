def test_tuple_in_rhs_must_be_collection_of_tuples_or_lists(self):
        test_cases = (
            (1, 2, 3),
            ((1, 2), (3, 4), None),
        )

        for rhs in test_cases:
            with self.subTest(rhs=rhs):
                with self.assertRaisesMessage(
                    ValueError,
                    "'in' lookup of ('customer_code', 'company_code') "
                    "must be a collection of tuples or lists",
                ):
                    TupleIn((F("customer_code"), F("company_code")), rhs)