def test_isnull_subquery(self):
        with self.assertRaisesMessage(
            ValueError, "'isnull' doesn't support multi-column subqueries."
        ):
            subquery = Customer.objects.filter(id=0)[:1]
            self.assertSequenceEqual(
                Contact.objects.filter(customer__isnull=subquery).order_by("id"), ()
            )