def test_getitem(self):
        choices = SimpleChoiceIterator()
        for i, expected in [(0, (1, "Item #1")), (-1, (3, "Item #3"))]:
            with self.subTest(index=i):
                self.assertEqual(choices[i], expected)