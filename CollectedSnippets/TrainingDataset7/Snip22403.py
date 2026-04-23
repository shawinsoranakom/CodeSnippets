def test_tuple_in_subquery_must_have_2_fields(self):
        lhs = (F("customer_code"), F("company_code"))
        rhs = Customer.objects.values_list("customer_id").query
        msg = (
            "The QuerySet value for the 'in' lookup must have 2 selected "
            "fields (received 1)"
        )
        with self.assertRaisesMessage(ValueError, msg):
            TupleIn(lhs, rhs)