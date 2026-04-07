def test_regex_backreferencing(self):
        # grouping and backreferences
        now = datetime.now()
        Article.objects.bulk_create(
            [
                Article(pub_date=now, headline="foobar"),
                Article(pub_date=now, headline="foobaz"),
                Article(pub_date=now, headline="ooF"),
                Article(pub_date=now, headline="foobarbaz"),
                Article(pub_date=now, headline="zoocarfaz"),
                Article(pub_date=now, headline="barfoobaz"),
                Article(pub_date=now, headline="bazbaRFOO"),
            ]
        )
        self.assertQuerySetEqual(
            Article.objects.filter(headline__regex=r"b(.).*b\1").values_list(
                "headline", flat=True
            ),
            ["barfoobaz", "bazbaRFOO", "foobarbaz"],
        )