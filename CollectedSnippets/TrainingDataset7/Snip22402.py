def test_tuple_in_subquery_must_be_query(self):
        lhs = (F("customer_code"), F("company_code"))
        # If rhs is any non-Query object with an as_sql() function.
        rhs = In(F("customer_code"), [1, 2, 3])
        with self.assertRaisesMessage(
            ValueError,
            "'in' subquery lookup of ('customer_code', 'company_code') "
            "must be a Query object (received 'In')",
        ):
            TupleIn(lhs, rhs)