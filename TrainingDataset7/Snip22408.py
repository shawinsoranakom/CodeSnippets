def test_lt_subquery(self):
        with self.assertRaisesMessage(
            ValueError, "'lt' doesn't support multi-column subqueries."
        ):
            subquery = Customer.objects.filter(id=self.customer_1.id)[:1]
            self.assertSequenceEqual(
                Contact.objects.filter(customer__lt=subquery).order_by("id"), ()
            )