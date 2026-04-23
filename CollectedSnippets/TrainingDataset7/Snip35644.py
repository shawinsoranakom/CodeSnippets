def test_update_annotated_multi_table_queryset(self):
        """
        Update of a queryset that's been annotated and involves multiple
        tables.
        """
        # Trivial annotated update
        qs = DataPoint.objects.annotate(related_count=Count("relatedpoint"))
        self.assertEqual(qs.update(value="Foo"), 3)
        # Update where annotation is used for filtering
        qs = DataPoint.objects.annotate(related_count=Count("relatedpoint"))
        self.assertEqual(qs.filter(related_count=1).update(value="Foo"), 1)
        # Update where aggregation annotation is used in update parameters
        qs = RelatedPoint.objects.annotate(max=Max("data__value"))
        msg = "Joined field references are not permitted in this query"
        with self.assertRaisesMessage(FieldError, msg):
            qs.update(name=F("max"))