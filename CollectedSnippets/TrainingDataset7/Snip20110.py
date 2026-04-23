def test_author_get(self):
        self.assertEqual(self.a1, Author.objects.get(first_name__exact="John"))