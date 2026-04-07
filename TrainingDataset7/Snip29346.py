def test_random_ordering(self):
        """
        Use '?' to order randomly.
        """
        self.assertEqual(len(list(Article.objects.order_by("?"))), 4)