def test_datetimes_has_lazy_iterator(self):
        pub_dates = [
            datetime.datetime(2005, 7, 28, 12, 15),
            datetime.datetime(2005, 7, 29, 2, 15),
            datetime.datetime(2005, 7, 30, 5, 15),
            datetime.datetime(2005, 7, 31, 19, 15),
        ]
        for i, pub_date in enumerate(pub_dates):
            Article(pub_date=pub_date, title="title #{}".format(i)).save()
        # Use iterator() with datetimes() to return a generator that lazily
        # requests each result one at a time, to save memory.
        dates = []
        with self.assertNumQueries(0):
            article_datetimes_iterator = Article.objects.datetimes(
                "pub_date", "day", order="DESC"
            ).iterator()

        with self.assertNumQueries(1):
            for article in article_datetimes_iterator:
                dates.append(article)
        self.assertEqual(
            dates,
            [
                datetime.datetime(2005, 7, 31, 0, 0),
                datetime.datetime(2005, 7, 30, 0, 0),
                datetime.datetime(2005, 7, 29, 0, 0),
                datetime.datetime(2005, 7, 28, 0, 0),
            ],
        )