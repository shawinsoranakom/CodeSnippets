def test_in_bulk_values_list_empty(self):
        arts = Article.objects.values_list().in_bulk([])
        self.assertEqual(arts, {})