def test_aggregate_in_order_by(self):
        msg = (
            "Using an aggregate in order_by() without also including it in "
            "annotate() is not allowed: Avg(F(book__rating)"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Author.objects.values("age").order_by(Avg("book__rating"))