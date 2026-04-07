def test_exact_subquery(self):
        msg = (
            "The QuerySet value for the exact lookup must have 2 selected "
            "fields (received 1)"
        )
        with self.assertRaisesMessage(ValueError, msg):
            subquery = Customer.objects.filter(id=self.customer_1.id)[:1]
            self.assertSequenceEqual(
                Contact.objects.filter(customer=subquery).order_by("id"), ()
            )