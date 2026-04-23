def test_dates_trunc_datetime_fields(self):
        Article.objects.bulk_create(
            Article(pub_date=pub_datetime.date(), pub_datetime=pub_datetime)
            for pub_datetime in [
                datetime.datetime(2015, 10, 21, 18, 1),
                datetime.datetime(2015, 10, 21, 18, 2),
                datetime.datetime(2015, 10, 22, 18, 1),
                datetime.datetime(2015, 10, 22, 18, 2),
            ]
        )
        self.assertSequenceEqual(
            Article.objects.dates("pub_datetime", "day", order="ASC"),
            [
                datetime.date(2015, 10, 21),
                datetime.date(2015, 10, 22),
            ],
        )