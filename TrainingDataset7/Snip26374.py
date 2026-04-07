def test_select_related(self):
        # Article.objects.select_related().dates() works properly when there
        # are multiple Articles with the same date but different foreign-key
        # objects (Reporters).
        r1 = Reporter.objects.create(
            first_name="Mike", last_name="Royko", email="royko@suntimes.com"
        )
        r2 = Reporter.objects.create(
            first_name="John", last_name="Kass", email="jkass@tribune.com"
        )
        Article.objects.create(
            headline="First", pub_date=datetime.date(1980, 4, 23), reporter=r1
        )
        Article.objects.create(
            headline="Second", pub_date=datetime.date(1980, 4, 23), reporter=r2
        )
        self.assertEqual(
            list(Article.objects.select_related().dates("pub_date", "day")),
            [datetime.date(1980, 4, 23), datetime.date(2005, 7, 27)],
        )
        self.assertEqual(
            list(Article.objects.select_related().dates("pub_date", "month")),
            [datetime.date(1980, 4, 1), datetime.date(2005, 7, 1)],
        )
        self.assertEqual(
            list(Article.objects.select_related().dates("pub_date", "year")),
            [datetime.date(1980, 1, 1), datetime.date(2005, 1, 1)],
        )