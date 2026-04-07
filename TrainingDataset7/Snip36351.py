def test_lazy_repr_bytes(self):
        original_object = b"J\xc3\xbcst a str\xc3\xadng"
        lazy_obj = lazy(lambda: original_object, bytes)
        self.assertEqual(repr(original_object), repr(lazy_obj()))