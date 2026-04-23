def test_exact(self):
        test_cases = (
            (self.customer_1, (self.contact_1, self.contact_2, self.contact_5)),
            (self.customer_2, (self.contact_3,)),
            (self.customer_3, (self.contact_4,)),
            (self.customer_4, ()),
            (self.customer_5, (self.contact_6,)),
        )

        for customer, contacts in test_cases:
            with self.subTest(
                "filter(customer=customer)",
                customer=customer,
                contacts=contacts,
            ):
                self.assertSequenceEqual(
                    Contact.objects.filter(customer=customer).order_by("id"), contacts
                )
            with self.subTest(
                "filter(TupleExact)",
                customer=customer,
                contacts=contacts,
            ):
                lhs = (F("customer_code"), F("company_code"))
                rhs = (customer.customer_id, customer.company)
                lookup = TupleExact(lhs, rhs)
                self.assertSequenceEqual(
                    Contact.objects.filter(lookup).order_by("id"), contacts
                )