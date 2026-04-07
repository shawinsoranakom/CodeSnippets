def test_refresh_overwrites_queryset_fields(self):
        a = Article.objects.create(pub_date=datetime.now())
        headline = "headline"
        Article.objects.filter(pk=a.pk).update(headline=headline)

        from_queryset = Article.objects.only("pub_date")
        with self.assertNumQueries(1):
            a.refresh_from_db(from_queryset=from_queryset)
            self.assertNotEqual(a.headline, headline)
        with self.assertNumQueries(1):
            a.refresh_from_db(fields=["headline"], from_queryset=from_queryset)
            self.assertEqual(a.headline, headline)