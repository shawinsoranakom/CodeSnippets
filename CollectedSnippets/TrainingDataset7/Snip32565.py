def test_case_insensitive(self):
        "Model names are case insensitive. Model swapping honors this."
        Article.objects.all()
        self.assertIsNone(Article._meta.swapped)