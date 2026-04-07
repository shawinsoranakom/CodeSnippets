def test_queryset_delete_removes_all_items_in_that_queryset(self):
        headlines = ["An article", "Article One", "Amazing article", "Boring article"]
        some_pub_date = datetime(2014, 5, 16, 12, 1)
        for headline in headlines:
            Article(headline=headline, pub_date=some_pub_date).save()
        self.assertQuerySetEqual(
            Article.objects.order_by("headline"),
            sorted(headlines),
            transform=lambda a: a.headline,
        )
        Article.objects.filter(headline__startswith="A").delete()
        self.assertEqual(Article.objects.get().headline, "Boring article")