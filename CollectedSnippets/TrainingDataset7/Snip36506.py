def test_getattr(self):
        obj = self.lazy_wrap(Foo())
        self.assertEqual(obj.foo, "bar")