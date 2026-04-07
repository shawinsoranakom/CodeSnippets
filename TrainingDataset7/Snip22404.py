def test_tuple_in_subquery(self):
        customers = Customer.objects.values_list("customer_id", "company")
        test_cases = (
            (self.customer_1, (self.contact_1, self.contact_2, self.contact_5)),
            (self.customer_2, (self.contact_3,)),
            (self.customer_3, (self.contact_4,)),
            (self.customer_4, ()),
            (self.customer_5, (self.contact_6,)),
        )

        for customer, contacts in test_cases:
            lhs = (F("customer_code"), F("company_code"))
            rhs = customers.filter(id=customer.id).query
            lookup = TupleIn(lhs, rhs)
            qs = Contact.objects.filter(lookup).order_by("id")

            with self.subTest(customer=customer.id, query=str(qs.query)):
                self.assertSequenceEqual(qs, contacts)