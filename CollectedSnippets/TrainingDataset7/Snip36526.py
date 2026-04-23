def test_pickle(self):
        # See ticket #16563
        obj = self.lazy_wrap(Foo())
        obj.bar = "baz"
        pickled = pickle.dumps(obj)
        unpickled = pickle.loads(pickled)
        self.assertIsInstance(unpickled, Foo)
        self.assertEqual(unpickled, obj)
        self.assertEqual(unpickled.foo, obj.foo)
        self.assertEqual(unpickled.bar, obj.bar)