def test_bulk_create_all_db_defaults(self):
        articles = [DBArticle(), DBArticle()]
        DBArticle.objects.bulk_create(articles)

        headlines = DBArticle.objects.values_list("headline", flat=True)
        self.assertSequenceEqual(headlines, ["Default headline", "Default headline"])