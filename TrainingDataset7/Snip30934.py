def test_pickle_prefetch_queryset_still_usable(self):
        g = Group.objects.create(name="foo")
        groups = Group.objects.prefetch_related(
            models.Prefetch("event_set", queryset=Event.objects.order_by("id"))
        )
        groups2 = pickle.loads(pickle.dumps(groups))
        self.assertSequenceEqual(groups2.filter(id__gte=0), [g])