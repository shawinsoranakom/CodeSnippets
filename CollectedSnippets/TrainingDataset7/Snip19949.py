def setUpTestData(cls):
        # Don't use the manager to ensure the site exists with pk=1, regardless
        # of whether or not it already exists.
        cls.site1 = Site(pk=1, domain="testserver", name="testserver")
        cls.site1.save()
        cls.author1 = Author.objects.create(name="Boris")
        cls.article1 = Article.objects.create(
            title="Old Article",
            slug="old_article",
            author=cls.author1,
            date_created=datetime.datetime(2001, 1, 1, 21, 22, 23),
        )
        cls.article2 = Article.objects.create(
            title="Current Article",
            slug="current_article",
            author=cls.author1,
            date_created=datetime.datetime(2007, 9, 17, 21, 22, 23),
        )
        cls.article3 = Article.objects.create(
            title="Future Article",
            slug="future_article",
            author=cls.author1,
            date_created=datetime.datetime(3000, 1, 1, 21, 22, 23),
        )
        cls.scheme1 = SchemeIncludedURL.objects.create(
            url="http://test_scheme_included_http/"
        )
        cls.scheme2 = SchemeIncludedURL.objects.create(
            url="https://test_scheme_included_https/"
        )
        cls.scheme3 = SchemeIncludedURL.objects.create(
            url="//test_default_scheme_kept/"
        )