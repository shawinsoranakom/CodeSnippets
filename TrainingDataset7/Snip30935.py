def test_pickle_prefetch_queryset_not_evaluated(self):
        Group.objects.create(name="foo")
        groups = Group.objects.prefetch_related(
            models.Prefetch("event_set", queryset=Event.objects.order_by("id"))
        )
        list(groups)  # evaluate QuerySet
        with self.assertNumQueries(0):
            pickle.loads(pickle.dumps(groups))