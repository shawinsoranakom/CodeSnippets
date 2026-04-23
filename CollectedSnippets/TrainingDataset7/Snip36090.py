def test_not_equal_superset(self):
        self.assertNotEqual(
            SimpleChoiceIterator(),
            [(1, "Item #1"), (2, "Item #2"), (3, "Item #3"), None],
        )