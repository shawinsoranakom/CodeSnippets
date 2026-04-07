def test_isnull(self):
        contacts = (
            self.contact_1,
            self.contact_2,
            self.contact_3,
            self.contact_4,
            self.contact_5,
            self.contact_6,
        )

        with self.subTest("filter(customer__isnull=True)"):
            self.assertSequenceEqual(
                Contact.objects.filter(customer__isnull=True).order_by("id"),
                (),
            )
        with self.subTest("filter(TupleIsNull(True))"):
            lhs = (F("customer_code"), F("company_code"))
            lookup = TupleIsNull(lhs, True)
            self.assertSequenceEqual(
                Contact.objects.filter(lookup).order_by("id"),
                (),
            )
        with self.subTest("filter(customer__isnull=False)"):
            self.assertSequenceEqual(
                Contact.objects.filter(customer__isnull=False).order_by("id"),
                contacts,
            )
        with self.subTest("filter(TupleIsNull(False))"):
            lhs = (F("customer_code"), F("company_code"))
            lookup = TupleIsNull(lhs, False)
            self.assertSequenceEqual(
                Contact.objects.filter(lookup).order_by("id"),
                contacts,
            )