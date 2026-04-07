def assert_filter_waiters(**params):
            self.assertSequenceEqual(Waiter.objects.filter(**params), [w])