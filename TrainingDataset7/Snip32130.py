def test_disconnect_in_dispatch(self):
        """
        Signals that disconnect when being called don't mess future
        dispatching.
        """

        class Handler:
            def __init__(self, param):
                self.param = param
                self._run = False

            def __call__(self, signal, sender, **kwargs):
                self._run = True
                signal.disconnect(receiver=self, sender=sender)

        a, b = Handler(1), Handler(2)
        signals.post_save.connect(a, sender=Person, weak=False)
        signals.post_save.connect(b, sender=Person, weak=False)
        Person.objects.create(first_name="John", last_name="Smith")

        self.assertTrue(a._run)
        self.assertTrue(b._run)
        self.assertEqual(signals.post_save.receivers, [])