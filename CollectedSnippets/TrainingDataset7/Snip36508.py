def test_setattr(self):
        obj = self.lazy_wrap(Foo())
        obj.foo = "BAR"
        obj.bar = "baz"
        self.assertEqual(obj.foo, "BAR")
        self.assertEqual(obj.bar, "baz")