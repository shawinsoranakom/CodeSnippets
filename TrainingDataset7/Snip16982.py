def test_aggregate_over_aggregate(self):
        msg = "Cannot compute Avg('age_agg'): 'age_agg' is an aggregate"
        with self.assertRaisesMessage(FieldError, msg):
            Author.objects.aggregate(
                age_agg=Sum(F("age")),
                avg_age=Avg(F("age_agg")),
            )