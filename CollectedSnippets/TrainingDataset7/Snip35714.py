def test_path_reverse_without_parameter(self):
        url = reverse("articles-2003")
        self.assertEqual(url, "/articles/2003/")