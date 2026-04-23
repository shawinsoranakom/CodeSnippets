def test_query_all_available_authors(self):
        self.assertSequenceEqual(Author.objects.all(), [self.a2, self.a1])