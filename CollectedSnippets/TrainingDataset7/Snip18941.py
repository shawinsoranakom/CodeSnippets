def test_manager_method_attributes(self):
        self.assertEqual(Article.objects.get.__doc__, models.QuerySet.get.__doc__)
        self.assertEqual(Article.objects.count.__name__, models.QuerySet.count.__name__)