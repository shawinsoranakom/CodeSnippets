def test_aggregate_referencing_aggregate(self):
        # Regression for #10766 - Shouldn't be able to reference an aggregate
        # fields in an aggregate() call.
        msg = "Cannot compute Avg('mean_age'): 'mean_age' is an aggregate"
        with self.assertRaisesMessage(FieldError, msg):
            Book.objects.annotate(mean_age=Avg("authors__age")).annotate(
                Avg("mean_age")
            )