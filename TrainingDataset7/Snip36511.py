def test_cmp(self):
        obj1 = self.lazy_wrap("foo")
        obj2 = self.lazy_wrap("bar")
        obj3 = self.lazy_wrap("foo")
        self.assertEqual(obj1, "foo")
        self.assertEqual(obj1, obj3)
        self.assertNotEqual(obj1, obj2)
        self.assertNotEqual(obj1, "bar")