def test_aggregate_alias(self):
        msg = (
            "Cannot aggregate over the 'other_age' alias. Use annotate() to promote it."
        )
        with self.assertRaisesMessage(FieldError, msg):
            Author.objects.alias(
                other_age=F("age"),
            ).aggregate(otherage_sum=Sum("other_age"))