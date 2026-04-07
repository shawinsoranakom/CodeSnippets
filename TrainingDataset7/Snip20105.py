def test_get_all_authors_for_an_article(self):
        self.assertSequenceEqual(self.article.authors.all(), [self.a2, self.a1])