def test_copy_list_no_evaluation(self):
        # Copying a list doesn't force evaluation.
        lst = [1, 2, 3]

        obj = self.lazy_wrap(lst)
        obj2 = copy.copy(obj)

        self.assertIsNot(obj, obj2)
        self.assertIs(obj._wrapped, empty)
        self.assertIs(obj2._wrapped, empty)