def test_getattribute(self):
        """
        Proxy methods don't exist on wrapped objects unless they're set.
        """
        attrs = [
            "__getitem__",
            "__setitem__",
            "__delitem__",
            "__iter__",
            "__len__",
            "__contains__",
        ]
        foo = Foo()
        obj = self.lazy_wrap(foo)
        for attr in attrs:
            with self.subTest(attr):
                self.assertFalse(hasattr(obj, attr))
                setattr(foo, attr, attr)
                obj_with_attr = self.lazy_wrap(foo)
                self.assertTrue(hasattr(obj_with_attr, attr))
                self.assertEqual(getattr(obj_with_attr, attr), attr)