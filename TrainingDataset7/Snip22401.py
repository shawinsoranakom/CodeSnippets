def test_in_subquery(self):
        subquery = Customer.objects.filter(id=self.customer_1.id)[:1]
        self.assertSequenceEqual(
            Contact.objects.filter(customer__in=subquery).order_by("id"),
            (self.contact_1, self.contact_2, self.contact_5),
        )