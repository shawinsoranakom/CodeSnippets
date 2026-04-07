def test_foreign_key(self):
        # Add a Waiter to the Restaurant.
        w = self.r1.waiter_set.create(name="Joe")
        self.assertEqual(
            repr(w), "<Waiter: Joe the waiter at Demon Dogs the restaurant>"
        )

        # Query the waiters
        def assert_filter_waiters(**params):
            self.assertSequenceEqual(Waiter.objects.filter(**params), [w])

        assert_filter_waiters(restaurant__place__exact=self.p1.pk)
        assert_filter_waiters(restaurant__place__exact=self.p1)
        assert_filter_waiters(restaurant__place__pk=self.p1.pk)
        assert_filter_waiters(restaurant__exact=self.r1.pk)
        assert_filter_waiters(restaurant__exact=self.r1)
        assert_filter_waiters(restaurant__pk=self.r1.pk)
        assert_filter_waiters(restaurant=self.r1.pk)
        assert_filter_waiters(restaurant=self.r1)
        assert_filter_waiters(id__exact=w.pk)
        assert_filter_waiters(pk=w.pk)
        # Delete the restaurant; the waiter should also be removed
        r = Restaurant.objects.get(pk=self.r1.pk)
        r.delete()
        self.assertEqual(Waiter.objects.count(), 0)