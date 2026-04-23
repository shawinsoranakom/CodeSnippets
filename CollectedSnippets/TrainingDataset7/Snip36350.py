def test_lazy_repr_int(self):
        original_object = 15
        lazy_obj = lazy(lambda: original_object, int)
        self.assertEqual(repr(original_object), repr(lazy_obj()))