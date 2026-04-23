def test_count_after_count_function(self):
        # Old-style count aggregations can be mixed with new-style
        self.assertEqual(Book.objects.annotate(num_authors=Count("authors")).count(), 6)