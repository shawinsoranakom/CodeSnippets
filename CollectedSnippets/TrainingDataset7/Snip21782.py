def test_bulk_create_mixed_db_defaults(self):
        articles = [DBArticle(), DBArticle(headline="Something else")]
        DBArticle.objects.bulk_create(articles)

        headlines = DBArticle.objects.values_list("headline", flat=True)
        self.assertCountEqual(headlines, ["Default headline", "Something else"])