def test_pickle_with_reduce(self):
        """
        Test in a fairly synthetic setting.
        """
        # Test every pickle protocol available
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            lazy_objs = [
                SimpleLazyObject(lambda: BaseBaz()),
                SimpleLazyObject(lambda: Baz(1)),
                SimpleLazyObject(lambda: BazProxy(Baz(2))),
            ]
            for obj in lazy_objs:
                pickled = pickle.dumps(obj, protocol)
                unpickled = pickle.loads(pickled)
                self.assertEqual(unpickled, obj)
                self.assertEqual(unpickled.baz, "right")