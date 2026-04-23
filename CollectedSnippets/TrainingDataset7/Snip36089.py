def test_not_equal_subset(self):
        self.assertNotEqual(SimpleChoiceIterator(), [(1, "Item #1"), (2, "Item #2")])