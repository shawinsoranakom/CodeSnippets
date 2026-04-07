def test_iterator_choices(self):
        """
        get_choices() works with Iterators.
        """
        self.assertEqual(WhizIter(c=1).c, 1)  # A nested value
        self.assertEqual(WhizIter(c=9).c, 9)  # Invalid value
        self.assertIsNone(WhizIter(c=None).c)  # Blank value
        self.assertEqual(WhizIter(c="").c, "")