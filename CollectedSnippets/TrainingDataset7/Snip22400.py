def test_in(self):
        cust_1, cust_2, cust_3, cust_4, cust_5 = (
            self.customer_1,
            self.customer_2,
            self.customer_3,
            self.customer_4,
            self.customer_5,
        )
        c1, c2, c3, c4, c5, c6 = (
            self.contact_1,
            self.contact_2,
            self.contact_3,
            self.contact_4,
            self.contact_5,
            self.contact_6,
        )
        test_cases = (
            ((), ()),
            ((cust_1,), (c1, c2, c5)),
            ((cust_1, cust_2), (c1, c2, c3, c5)),
            ((cust_1, cust_2, cust_3), (c1, c2, c3, c4, c5)),
            ((cust_1, cust_2, cust_3, cust_4), (c1, c2, c3, c4, c5)),
            ((cust_1, cust_2, cust_3, cust_4, cust_5), (c1, c2, c3, c4, c5, c6)),
        )

        for customers, contacts in test_cases:
            with self.subTest(
                "filter(customer__in=customers)",
                customers=customers,
                contacts=contacts,
            ):
                self.assertSequenceEqual(
                    Contact.objects.filter(customer__in=customers).order_by("id"),
                    contacts,
                )
            with self.subTest(
                "filter(TupleIn)",
                customers=customers,
                contacts=contacts,
            ):
                lhs = (F("customer_code"), F("company_code"))
                rhs = [(c.customer_id, c.company) for c in customers]
                lookup = TupleIn(lhs, rhs)
                self.assertSequenceEqual(
                    Contact.objects.filter(lookup).order_by("id"), contacts
                )