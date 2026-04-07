def test_refresh_clears_reverse_related_explicit_fields(self):
        article = Article.objects.create(headline="Test", pub_date=datetime(2024, 2, 4))
        self.assertFalse(hasattr(article, "featured"))
        FeaturedArticle.objects.create(article_id=article.pk)
        article.refresh_from_db(fields=["featured"])
        self.assertTrue(hasattr(article, "featured"))