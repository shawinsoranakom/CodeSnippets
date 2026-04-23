def test_lazy_repr_text(self):
        original_object = "Lazy translation text"
        lazy_obj = lazy(lambda: original_object, str)
        self.assertEqual(repr(original_object), repr(lazy_obj()))