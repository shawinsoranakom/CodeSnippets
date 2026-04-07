def test_in_bulk_values_empty(self):
        arts = Article.objects.values().in_bulk([])
        self.assertEqual(arts, {})