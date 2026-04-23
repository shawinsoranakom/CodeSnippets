def test_gte(self):
        c1, c2, c3, c4, c5, c6 = (
            self.contact_1,
            self.contact_2,
            self.contact_3,
            self.contact_4,
            self.contact_5,
            self.contact_6,
        )
        test_cases = (
            (self.customer_1, (c1, c2, c3, c4, c5, c6)),
            (self.customer_2, (c3, c4, c6)),
            (self.customer_5, (c4, c6)),
            (self.customer_3, (c4,)),
            (self.customer_4, ()),
        )

        for customer, contacts in test_cases:
            with self.subTest(
                "filter(customer__gte=customer)",
                customer=customer,
                contacts=contacts,
            ):
                self.assertSequenceEqual(
                    Contact.objects.filter(customer__gte=customer).order_by("pk"),
                    contacts,
                )
            with self.subTest(
                "filter(TupleGreaterThanOrEqual)",
                customer=customer,
                contacts=contacts,
            ):
                lhs = (F("customer_code"), F("company_code"))
                rhs = (customer.customer_id, customer.company)
                lookup = TupleGreaterThanOrEqual(lhs, rhs)
                self.assertSequenceEqual(
                    Contact.objects.filter(lookup).order_by("id"), contacts
                )