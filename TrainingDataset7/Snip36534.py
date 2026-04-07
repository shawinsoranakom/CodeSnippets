def test_deepcopy_class_no_evaluation(self):
        # Deep copying doesn't force evaluation.
        foo = Foo()

        obj = self.lazy_wrap(foo)
        obj2 = copy.deepcopy(obj)

        self.assertIsNot(obj, obj2)
        self.assertIs(obj._wrapped, empty)
        self.assertIs(obj2._wrapped, empty)