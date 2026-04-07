def test_refresh_with_related(self):
        a = Article.objects.create(pub_date=datetime.now())
        fa = FeaturedArticle.objects.create(article=a)

        from_queryset = FeaturedArticle.objects.select_related("article")
        with self.assertNumQueries(1):
            fa.refresh_from_db(from_queryset=from_queryset)
            self.assertEqual(fa.article.pub_date, a.pub_date)
        with self.assertNumQueries(2):
            fa.refresh_from_db()
            self.assertEqual(fa.article.pub_date, a.pub_date)