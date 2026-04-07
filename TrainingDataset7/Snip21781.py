def test_bulk_create_all_db_defaults_one_field(self):
        pub_date = datetime.now()
        articles = [DBArticle(pub_date=pub_date), DBArticle(pub_date=pub_date)]
        DBArticle.objects.bulk_create(articles)

        headlines = DBArticle.objects.values_list("headline", "pub_date", "cost")
        self.assertSequenceEqual(
            headlines,
            [
                ("Default headline", pub_date, Decimal("3.33")),
                ("Default headline", pub_date, Decimal("3.33")),
            ],
        )