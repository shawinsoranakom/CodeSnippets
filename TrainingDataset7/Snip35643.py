def test_update_annotated_queryset(self):
        """
        Update of a queryset that's been annotated.
        """
        # Trivial annotated update
        qs = DataPoint.objects.annotate(alias=F("value"))
        self.assertEqual(qs.update(another_value="foo"), 3)
        # Update where annotation is used for filtering
        qs = DataPoint.objects.annotate(alias=F("value")).filter(alias="apple")
        self.assertEqual(qs.update(another_value="foo"), 1)
        # Update where annotation is used in update parameters
        qs = DataPoint.objects.annotate(alias=F("value"))
        self.assertEqual(qs.update(another_value=F("alias")), 3)
        # Update where aggregation annotation is used in update parameters
        qs = DataPoint.objects.annotate(max=Max("value"))
        msg = (
            "Aggregate functions are not allowed in this query "
            "(another_value=Max(Col(update_datapoint, update.DataPoint.value)))."
        )
        with self.assertRaisesMessage(FieldError, msg):
            qs.update(another_value=F("max"))