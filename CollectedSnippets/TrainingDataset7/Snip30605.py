def test_tickets_7204_7506(self):
        # Make sure querysets with related fields can be pickled. If this
        # doesn't crash, it's a Good Thing.
        pickle.dumps(Item.objects.all())