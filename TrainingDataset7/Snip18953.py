def test_refresh_clears_reverse_related(self):
        """refresh_from_db() clear cached reverse relations."""
        article = Article.objects.create(
            headline="Parrot programs in Python",
            pub_date=datetime(2005, 7, 28),
        )
        self.assertFalse(hasattr(article, "featured"))
        FeaturedArticle.objects.create(article_id=article.pk)
        article.refresh_from_db()
        self.assertTrue(hasattr(article, "featured"))