def test_copy_list(self):
        # Copying a list works and returns the correct objects.
        lst = [1, 2, 3]

        obj = self.lazy_wrap(lst)
        len(lst)  # forces evaluation
        obj2 = copy.copy(obj)

        self.assertIsNot(obj, obj2)
        self.assertIsInstance(obj2, list)
        self.assertEqual(obj2, [1, 2, 3])