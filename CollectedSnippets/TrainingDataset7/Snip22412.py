def test_gt_subquery(self):
        with self.assertRaisesMessage(
            ValueError, "'gt' doesn't support multi-column subqueries."
        ):
            subquery = Customer.objects.filter(id=self.customer_1.id)[:1]
            self.assertSequenceEqual(
                Contact.objects.filter(customer__gt=subquery).order_by("id"), ()
            )