def test_pickle_prefetch_related_idempotence(self):
        g = Group.objects.create(name="foo")
        groups = Group.objects.prefetch_related("event_set")

        # First pickling
        groups = pickle.loads(pickle.dumps(groups))
        self.assertSequenceEqual(groups, [g])

        # Second pickling
        groups = pickle.loads(pickle.dumps(groups))
        self.assertSequenceEqual(groups, [g])