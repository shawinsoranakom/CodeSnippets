def setUpTestData(cls):
        # Create a few Reporters.
        cls.r = Reporter(first_name="John", last_name="Smith", email="john@example.com")
        cls.r.save()
        cls.r2 = Reporter(
            first_name="Paul", last_name="Jones", email="paul@example.com"
        )
        cls.r2.save()
        # Create an Article.
        cls.a = Article(
            headline="This is a test",
            pub_date=datetime.date(2005, 7, 27),
            reporter=cls.r,
        )
        cls.a.save()