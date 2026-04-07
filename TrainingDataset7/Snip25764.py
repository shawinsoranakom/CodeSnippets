def test_count(self):
        # count() returns the number of objects matching search criteria.
        self.assertEqual(Article.objects.count(), 7)
        self.assertEqual(
            Article.objects.filter(pub_date__exact=datetime(2005, 7, 27)).count(), 3
        )
        self.assertEqual(
            Article.objects.filter(headline__startswith="Blah blah").count(), 0
        )

        # count() should respect sliced query sets.
        articles = Article.objects.all()
        self.assertEqual(articles.count(), 7)
        self.assertEqual(articles[:4].count(), 4)
        self.assertEqual(articles[1:100].count(), 6)
        self.assertEqual(articles[10:100].count(), 0)

        # Date and date/time lookups can also be done with strings.
        self.assertEqual(
            Article.objects.filter(pub_date__exact="2005-07-27 00:00:00").count(), 3
        )