def test_gte_subquery(self):
        with self.assertRaisesMessage(
            ValueError, "'gte' doesn't support multi-column subqueries."
        ):
            subquery = Customer.objects.filter(id=self.customer_1.id)[:1]
            self.assertSequenceEqual(
                Contact.objects.filter(customer__gte=subquery).order_by("id"), ()
            )