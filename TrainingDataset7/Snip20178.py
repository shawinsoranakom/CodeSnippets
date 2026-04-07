def test_instance_related_lookup(self):
        article_author = Article._meta.get_field("author")
        with register_lookup(article_author, RelatedMoreThan):
            self.assertEqual(article_author.get_lookup("rmt"), RelatedMoreThan)
        self.assertIsNone(article_author.get_lookup("rmt"))