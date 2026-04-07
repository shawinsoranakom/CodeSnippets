def __call__(self, signal, sender, **kwargs):
        # Although test runner calls migrate for several databases,
        # testing for only one of them is quite sufficient.
        if kwargs["using"] == MIGRATE_DATABASE:
            self.call_counter += 1
            self.call_args = kwargs
            # we need to test only one call of migrate
            self.signal.disconnect(self, sender=APP_CONFIG)