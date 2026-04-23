def test_first_from_unordered_queryset_aggregation_pk_incomplete(self):
        msg = (
            "Cannot use QuerySet.first() on an unordered queryset performing "
            "aggregation. Add an ordering with order_by()."
        )
        with self.assertRaisesMessage(TypeError, msg):
            Comment.objects.values("tenant").annotate(max=Max("id")).first()