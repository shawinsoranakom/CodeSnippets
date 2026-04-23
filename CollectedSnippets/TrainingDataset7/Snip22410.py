def test_lte_subquery(self):
        with self.assertRaisesMessage(
            ValueError, "'lte' doesn't support multi-column subqueries."
        ):
            subquery = Customer.objects.filter(id=self.customer_1.id)[:1]
            self.assertSequenceEqual(
                Contact.objects.filter(customer__lte=subquery).order_by("id"), ()
            )