def test_eq(self):
        unrolled = [(1, "Item #1"), (2, "Item #2"), (3, "Item #3")]
        self.assertEqual(SimpleChoiceIterator(), unrolled)
        self.assertEqual(unrolled, SimpleChoiceIterator())