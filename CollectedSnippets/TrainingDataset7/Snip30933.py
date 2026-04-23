def test_pickle_prefetch_queryset_usable_outside_of_prefetch(self):
        # Prefetch shouldn't affect the fetch-on-pickle behavior of the
        # queryset passed to it.
        Group.objects.create(name="foo")
        events = Event.objects.order_by("id")
        Group.objects.prefetch_related(models.Prefetch("event_set", queryset=events))
        with self.assertNumQueries(1):
            events2 = pickle.loads(pickle.dumps(events))
        with self.assertNumQueries(0):
            list(events2)