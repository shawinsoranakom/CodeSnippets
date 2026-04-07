def test_in_empty_list(self):
        self.assertSequenceEqual(Article.objects.filter(id__in=[]), [])