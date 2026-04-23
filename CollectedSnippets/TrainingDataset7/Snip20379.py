def test_extract_outerref_validation(self):
        inner_qs = DTModel.objects.filter(name=ExtractMonth(OuterRef("name")))
        msg = (
            "Extract input expression must be DateField, DateTimeField, "
            "TimeField, or DurationField."
        )
        with self.assertRaisesMessage(ValueError, msg):
            DTModel.objects.annotate(related_name=Subquery(inner_qs.values("name")[:1]))