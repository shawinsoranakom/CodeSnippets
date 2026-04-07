def test_copy_class_no_evaluation(self):
        # Copying a class doesn't force evaluation.
        foo = Foo()

        obj = self.lazy_wrap(foo)
        obj2 = copy.copy(obj)

        self.assertIsNot(obj, obj2)
        self.assertIs(obj._wrapped, empty)
        self.assertIs(obj2._wrapped, empty)