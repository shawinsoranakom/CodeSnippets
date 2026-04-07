def test_empty_iterator_choices(self):
        """
        get_choices() works with empty iterators.
        """
        self.assertEqual(WhizIterEmpty(c="a").c, "a")  # A nested value
        self.assertEqual(WhizIterEmpty(c="b").c, "b")  # Invalid value
        self.assertIsNone(WhizIterEmpty(c=None).c)  # Blank value
        self.assertEqual(WhizIterEmpty(c="").c, "")