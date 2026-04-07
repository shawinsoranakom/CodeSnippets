def test_in_bulk_values_list_flat_empty(self):
        with ignore_warnings(category=RemovedInDjango70Warning):
            arts = Article.objects.values_list(flat=True).in_bulk([])
        self.assertEqual(arts, {})