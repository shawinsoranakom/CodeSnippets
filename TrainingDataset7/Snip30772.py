def test_can_get_number_of_items_in_queryset_using_standard_len(self):
        self.assertEqual(len(Article.objects.filter(name__exact="Article 1")), 1)