def test_tuple_in_rhs_must_have_2_elements_each(self):
        test_cases = (
            ((),),
            ((1,),),
            ((1, 2, 3),),
        )

        for rhs in test_cases:
            with self.subTest(rhs=rhs):
                with self.assertRaisesMessage(
                    ValueError,
                    "'in' lookup of ('customer_code', 'company_code') "
                    "must have 2 elements each",
                ):
                    TupleIn((F("customer_code"), F("company_code")), rhs)