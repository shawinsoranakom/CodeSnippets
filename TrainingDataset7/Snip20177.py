def test_related_lookup(self):
        article_author = Article._meta.get_field("author")
        with register_lookup(models.Field, CustomStartsWith):
            self.assertIsNone(article_author.get_lookup("sw"))
        with register_lookup(models.ForeignKey, RelatedMoreThan):
            self.assertEqual(article_author.get_lookup("rmt"), RelatedMoreThan)