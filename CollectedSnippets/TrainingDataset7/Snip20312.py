def test_datetimes_returns_available_dates_for_given_scope_and_given_field(self):
        pub_dates = [
            datetime.datetime(2005, 7, 28, 12, 15),
            datetime.datetime(2005, 7, 29, 2, 15),
            datetime.datetime(2005, 7, 30, 5, 15),
            datetime.datetime(2005, 7, 31, 19, 15),
        ]
        for i, pub_date in enumerate(pub_dates):
            Article(pub_date=pub_date, title="title #{}".format(i)).save()

        self.assertSequenceEqual(
            Article.objects.datetimes("pub_date", "year"),
            [datetime.datetime(2005, 1, 1, 0, 0)],
        )
        self.assertSequenceEqual(
            Article.objects.datetimes("pub_date", "month"),
            [datetime.datetime(2005, 7, 1, 0, 0)],
        )
        self.assertSequenceEqual(
            Article.objects.datetimes("pub_date", "week"),
            [datetime.datetime(2005, 7, 25, 0, 0)],
        )
        self.assertSequenceEqual(
            Article.objects.datetimes("pub_date", "day"),
            [
                datetime.datetime(2005, 7, 28, 0, 0),
                datetime.datetime(2005, 7, 29, 0, 0),
                datetime.datetime(2005, 7, 30, 0, 0),
                datetime.datetime(2005, 7, 31, 0, 0),
            ],
        )
        self.assertSequenceEqual(
            Article.objects.datetimes("pub_date", "day", order="ASC"),
            [
                datetime.datetime(2005, 7, 28, 0, 0),
                datetime.datetime(2005, 7, 29, 0, 0),
                datetime.datetime(2005, 7, 30, 0, 0),
                datetime.datetime(2005, 7, 31, 0, 0),
            ],
        )
        self.assertSequenceEqual(
            Article.objects.datetimes("pub_date", "day", order="DESC"),
            [
                datetime.datetime(2005, 7, 31, 0, 0),
                datetime.datetime(2005, 7, 30, 0, 0),
                datetime.datetime(2005, 7, 29, 0, 0),
                datetime.datetime(2005, 7, 28, 0, 0),
            ],
        )