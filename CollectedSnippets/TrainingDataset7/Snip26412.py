def setUpTestData(cls):
        # Create a Reporter.
        cls.r = Reporter(name="John Smith")
        cls.r.save()
        # Create an Article.
        cls.a = Article(headline="First", reporter=cls.r)
        cls.a.save()
        # Create an Article via the Reporter object.
        cls.a2 = cls.r.article_set.create(headline="Second")
        # Create an Article with no Reporter by passing "reporter=None".
        cls.a3 = Article(headline="Third", reporter=None)
        cls.a3.save()
        # Create another article and reporter
        cls.r2 = Reporter(name="Paul Jones")
        cls.r2.save()
        cls.a4 = cls.r2.article_set.create(headline="Fourth")