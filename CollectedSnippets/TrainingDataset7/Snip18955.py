def test_refresh_clears_one_to_one_field(self):
        article = Article.objects.create(
            headline="Parrot programs in Python",
            pub_date=datetime(2005, 7, 28),
        )
        featured = FeaturedArticle.objects.create(article_id=article.pk)
        self.assertEqual(featured.article.headline, "Parrot programs in Python")
        article.headline = "Parrot programs in Python 2.0"
        article.save()
        featured.refresh_from_db()
        self.assertEqual(featured.article.headline, "Parrot programs in Python 2.0")