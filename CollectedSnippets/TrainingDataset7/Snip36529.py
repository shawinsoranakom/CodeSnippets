def test_copy_class(self):
        # Copying a class works and returns the correct objects.
        foo = Foo()

        obj = self.lazy_wrap(foo)
        str(foo)  # forces evaluation
        obj2 = copy.copy(obj)

        self.assertIsNot(obj, obj2)
        self.assertIsInstance(obj2, Foo)
        self.assertEqual(obj2, Foo())